from pathlib import Path
import subprocess
from typing import Optional



from config import OPENABE_CONTAINER, OPENABE_WORKDIR, OPENABE_BINARY


LD_PATH = "/openabe/deps/root/lib:/openabe/root/lib:/usr/local/lib:$LD_LIBRARY_PATH"
CIPHERTEXT_PATH = f"{OPENABE_WORKDIR}/state/ciphertext.bin"


class OpenABEClient:
    """
    Python wrapper for the existing OpenABE CP-ABE test binary.

    This class does not implement ABE in Python. It calls the real OpenABE
    binary inside the Docker container and exchanges plaintext/ciphertext
    through environment variables and state files.
    """

    def __init__(
        self,
        container: str = OPENABE_CONTAINER,
        workdir: str = OPENABE_WORKDIR,
        binary: str = OPENABE_BINARY,
        timeout: int = 60,
    ):
        self.container = container
        self.workdir = workdir
        self.binary = binary
        self.timeout = timeout

    def _run(
        self,
        command: str,
        env_vars: Optional[dict] = None,
        input_text: Optional[str] = None,
    ):
        cmd = ["docker", "exec"]

        if env_vars:
            for key, value in env_vars.items():
                cmd.extend(["-e", f"{key}={value}"])

        if input_text is not None:
            cmd.append("-i")

        cmd.extend([
            self.container,
            "bash",
            "-lc",
            command,
        ])

        try:
            result = subprocess.run(
                cmd,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                "OpenABE command timed out.\n"
                f"Command: {' '.join(cmd)}\n"
                f"Timeout: {self.timeout} seconds"
            ) from exc

        if result.returncode != 0:
            raise RuntimeError(
                "OpenABE command failed.\n"
                f"Command: {' '.join(cmd)}\n\n"
                f"STDOUT:\n{result.stdout}\n\n"
                f"STDERR:\n{result.stderr}"
            )

        return result.stdout.strip(), result.stderr.strip()

    def check_container(self):
        """
        Checks whether the OpenABE container and cpabe_split binary are available.
        """
        command = (
            f"cd {self.workdir} && "
            f"pwd && "
            f"ls -l {self.binary}"
        )
        stdout, _ = self._run(command)
        return stdout

    def setup(self):
        """
        Generates CP-ABE public/master parameters using the existing cpabe_split binary.
        """
        command = (
            f"cd {self.workdir} && "
            f"export LD_LIBRARY_PATH={LD_PATH} && "
            f"{self.binary} setup"
        )
        stdout, stderr = self._run(command)
        return stdout, stderr

    def keygen(self, attributes: str):
        """
        Generates a user secret key for the given attribute set.

        Examples:
            attributes='|attr1'
            attributes='|attr1|attr2|attr3'
        """
        if not attributes:
            raise ValueError("attributes cannot be empty")

        command = (
            f"cd {self.workdir} && "
            f"export LD_LIBRARY_PATH={LD_PATH} && "
            f"{self.binary} keygen"
        )

        stdout, stderr = self._run(
            command,
            env_vars={
                "OPENABE_ATTRS": attributes,
            },
        )

        return stdout, stderr

    def encrypt(self, plaintext: str, policy: str):
        """
        Encrypts plaintext under an ABE access policy.
        The binary writes the ciphertext to state/ciphertext.bin.
        """
        if not plaintext:
            raise ValueError("plaintext cannot be empty")

        if not policy:
            raise ValueError("policy cannot be empty")

        command = (
            f"cd {self.workdir} && "
            f"export LD_LIBRARY_PATH={LD_PATH} && "
            f"{self.binary} encrypt"
        )

        stdout, stderr = self._run(
            command,
            env_vars={
                "OPENABE_MSG": plaintext,
                "OPENABE_POLICY": policy,
            },
        )

        self._ensure_ciphertext_exists()

        return stdout, stderr

    def decrypt_current_ciphertext(self):
        """
        Decrypts the current ciphertext stored at state/ciphertext.bin.
        """
        self._ensure_ciphertext_exists()

        command = (
            f"cd {self.workdir} && "
            f"export LD_LIBRARY_PATH={LD_PATH} && "
            f"{self.binary} decrypt"
        )

        stdout, stderr = self._run(command)
        return stdout, stderr

    def _ensure_ciphertext_exists(self):
        """
        Verifies that the ciphertext file exists and is not empty.
        """
        command = (
            f"test -s {CIPHERTEXT_PATH} && "
            f"stat -c%s {CIPHERTEXT_PATH}"
        )

        stdout, _ = self._run(command)
        size = int(stdout)

        if size <= 0:
            raise RuntimeError("ciphertext.bin exists but is empty")

    def read_ciphertext_b64(self) -> str:
        """
        Reads the current ciphertext file and returns it encoded in base64.
        """
        self._ensure_ciphertext_exists()

        stdout, _ = self._run(f"base64 -w 0 {CIPHERTEXT_PATH}")
        return stdout

    def write_ciphertext_b64(self, ciphertext_b64: str):
        """
        Writes a base64 ciphertext back into the OpenABE state/ciphertext.bin file.
        This allows the subscriber service to receive ciphertext via MQTT and then
        ask OpenABE to decrypt it.
        """
        if not ciphertext_b64:
            raise ValueError("ciphertext_b64 cannot be empty")

        command = (
            f"mkdir -p {self.workdir}/state && "
            f"base64 -d > {CIPHERTEXT_PATH}"
        )

        self._run(command, input_text=ciphertext_b64)
        self._ensure_ciphertext_exists()

        return CIPHERTEXT_PATH

    def ciphertext_size_bytes(self) -> int:
        self._ensure_ciphertext_exists()

        stdout, _ = self._run(f"stat -c%s {CIPHERTEXT_PATH}")
        return int(stdout)

    def encrypt_to_b64(self, plaintext: str, policy: str) -> dict:
        """
        Encrypts plaintext with OpenABE and returns the ciphertext as base64.
        """
        stdout, stderr = self.encrypt(plaintext, policy)

        ciphertext_b64 = self.read_ciphertext_b64()
        ciphertext_size = self.ciphertext_size_bytes()

        return {
            "ciphertext_b64": ciphertext_b64,
            "ciphertext_bin_bytes": ciphertext_size,
            "ciphertext_b64_bytes": len(ciphertext_b64.encode("utf-8")),
            "policy": policy,
            "stdout": stdout,
            "stderr": stderr,
        }

    def decrypt_from_b64(self, ciphertext_b64: str) -> str:
        """
        Writes the received ciphertext into the OpenABE container and decrypts it.
        """
        self.write_ciphertext_b64(ciphertext_b64)

        stdout, _ = self.decrypt_current_ciphertext()

        return stdout

    def export_usk_from_container(self, output_path: Path, source_path: str = "/openabe/examples/state/usk_key0.bin") -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        command = [
            "docker",
            "cp",
            f"{self.container}:{source_path}",
            str(output_path),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Failed to export OpenABE USK from container.\n"
                f"command: {' '.join(command)}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

        if not output_path.exists():
            raise FileNotFoundError(f"Exported USK file not found: {output_path}")

        return output_path