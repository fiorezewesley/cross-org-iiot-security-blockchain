from pathlib import Path
import subprocess
import json
import re
import os
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parents[2]
POC_DIR = PROJECT_DIR / "integrated-poc"
RUNTIME_DIR = POC_DIR / "runtime"
DEMO_RUNS_DIR = RUNTIME_DIR / "demo_runs"

OPENABE_CONTAINER = "openabe-lab-split-test"


st.set_page_config(
    page_title="IIoT ABE Blockchain PoC",
    layout="wide",
)


def run_command(command, cwd=PROJECT_DIR):
    result = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )

    output = ""

    if result.stdout:
        output += result.stdout

    if result.stderr:
        output += "\n[STDERR]\n" + result.stderr

    return result.returncode, output


def get_latest_demo_run():
    if not DEMO_RUNS_DIR.exists():
        return None

    runs = [item for item in DEMO_RUNS_DIR.iterdir() if item.is_dir()]

    if not runs:
        return None

    return sorted(runs, key=lambda item: item.stat().st_mtime, reverse=True)[0]


def get_latest_demo_summary():
    latest_run = get_latest_demo_run()

    if not latest_run:
        return None, None

    summary_path = latest_run / "demo_summary.json"

    if not summary_path.exists():
        return latest_run, None

    try:
        summary = json.loads(
            summary_path.read_text(encoding="utf-8", errors="ignore")
        )
        return latest_run, summary
    except Exception:
        return latest_run, None


def read_file(path: Path):
    if not path.exists():
        return None

    return path.read_text(encoding="utf-8", errors="ignore")


def extract_request_id_from_log(log_text: str):
    if not log_text:
        return None

    match = re.search(r"lastRequestId:\s*(\d+)", log_text)
    if match:
        return match.group(1)

    return None


def extract_recovered_payload(log_text: str):
    if not log_text:
        return None

    match = re.search(r"\[decrypt\] recovered message:\s*(\{.*\})", log_text)

    if not match:
        return None

    try:
        return json.loads(match.group(1))
    except Exception:
        return match.group(1)


def run_and_store(session_key, command):
    with st.spinner("Executando..."):
        returncode, output = run_command(command)

    st.session_state[session_key] = output
    st.session_state[f"{session_key}_returncode"] = returncode

    return returncode, output


def show_log(title, content, expanded=False):
    with st.expander(title, expanded=expanded):
        if content:
            st.code(content, language="text")
        else:
            st.info("Nenhum log disponível.")


def init_state():
    defaults = {
        "check_environment_log": "",
        "bootstrap_log": "",
        "request_access_log": "",
        "process_access_log": "",
        "decrypt_log": "",
        "full_demo_log": "",
        "last_request_id": "",
        "last_payload": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_guided_status():
    guided_request_id = st.session_state.get("last_request_id") or "-"

    process_log = st.session_state.get("process_access_log", "")
    decrypt_log = st.session_state.get("decrypt_log", "")

    process_ok = bool(
        process_log
        and "encrypted key grant completed successfully" in process_log
    )

    decrypt_ok = bool(
        decrypt_log
        and "[decrypt] recovered message:" in decrypt_log
    )

    return guided_request_id, process_ok, decrypt_ok


def show_execution_status():
    latest_run, latest_demo_summary = get_latest_demo_summary()

    guided_request_id, process_ok, decrypt_ok = get_guided_status()

    latest_demo_request_id = "-"

    if latest_demo_summary:
        latest_demo_request_id = latest_demo_summary.get("request_id", "-")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Request ID guiado", guided_request_id)

    with col2:
        st.metric("Chave ABE guiada", "Gerada" if process_ok else "Pendente")

    with col3:
        st.metric("Decrypt guiado", "Sucesso" if decrypt_ok else "Pendente")

    with col4:
        st.metric("Última demo completa", latest_demo_request_id)

    if (
        latest_demo_summary
        and guided_request_id != "-"
        and str(guided_request_id) != str(latest_demo_request_id)
    ):
        st.info(
            f"O fluxo guiado mais recente usa Request ID {guided_request_id}, "
            f"enquanto a última demo completa registrada usa Request ID {latest_demo_request_id}. "
            "Isso é esperado quando a demo completa não foi executada novamente após o fluxo guiado. "
            "Os dois valores representam execuções distintas da PoC."
        )


def process_access_request(request_id: str):
    full_log = ""

    commands = [
        (
            "Attribute Authority",
            "python3 integrated-poc/attribute_authority/attribute_authority_service.py --once",
        ),
        (
            "Recuperação da encUSK pelo subscriber",
            f"python3 integrated-poc/subscriber_crypto/retrieve_encrypted_usk.py --request-id {request_id}",
        ),
        (
            "Restauração da USK no container OpenABE",
            (
                f"docker cp integrated-poc/runtime/keys/consumer_001/usk_request_{request_id}.bin "
                f"{OPENABE_CONTAINER}:/openabe/examples/state/usk_key0.bin && "
                f"docker exec {OPENABE_CONTAINER} ls -lh /openabe/examples/state/usk_key0.bin"
            ),
        ),
    ]

    for title, command in commands:
        full_log += "\n" + "=" * 80 + "\n"
        full_log += f"{title}\n"
        full_log += "=" * 80 + "\n"
        full_log += f"COMMAND: {command}\n\n"

        returncode, output = run_command(command)
        full_log += output + "\n"

        if returncode != 0:
            full_log += f"\n[ERROR] Etapa interrompida. Código de retorno: {returncode}\n"
            st.session_state["process_access_log"] = full_log
            return returncode, full_log

    st.session_state["process_access_log"] = full_log
    return 0, full_log


init_state()


st.title("IIoT ABE Blockchain PoC")
st.caption("Interface de demonstração para Blockchain, OpenABE, ECIES e dados IIoT")

st.markdown(
    """
Esta interface organiza a execução da Prova de Conceito em um fluxo mais reprodutível.
As etapas técnicas continuam sendo executadas pelos scripts do projeto, mas a interface
centraliza a operação, os logs e as evidências.
"""
)

tab_dashboard, tab_flow, tab_full_demo, tab_evidence, tab_explanation = st.tabs(
    [
        "Visão geral",
        "Fluxo guiado",
        "Demo completa",
        "Evidências",
        "Explicação técnica",
    ]
)


with tab_dashboard:
    st.header("Visão geral da PoC")

    st.markdown(
        """
A PoC demonstra um fluxo de compartilhamento seguro de dados IIoT utilizando
blockchain para rastreabilidade, OpenABE para controle criptográfico de acesso
e ECIES para proteção da chave ABE entregue ao consumidor.
"""
    )

    show_execution_status()

    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Componentes principais")

        st.markdown(
            """
| Componente | Papel na PoC |
|---|---|
| Blockchain Besu | Registro de políticas, atributos, solicitações e grants |
| Smart Contract | Coordena os registros on-chain da arquitetura |
| Attribute Authority | Gera a chave ABE com os atributos do consumidor |
| OpenABE | Realiza criptografia e descriptografia baseada em atributos |
| ECIES | Protege a entrega da chave ABE ao consumidor |
| Subscriber | Recupera a chave protegida e tenta descriptografar o dado |
"""
        )

    with col2:
        st.subheader("Resultado da última descriptografia guiada")

        payload = st.session_state.get("last_payload")

        if payload:
            st.json(payload)
        else:
            st.info("Nenhum payload descriptografado nesta sessão guiada.")


with tab_flow:
    st.header("Fluxo guiado")

    st.markdown(
        """
Execute a PoC em etapas. As ações internas de recuperação da chave e restauração
da USK no container são automatizadas dentro da etapa de processamento da solicitação.
"""
    )

    show_execution_status()

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("1. Ambiente")

        if st.button("Verificar ambiente", use_container_width=True):
            returncode, output = run_and_store(
                "check_environment_log",
                "python3 integrated-poc/scripts/check_environment.py",
            )

            if returncode == 0:
                st.success("Ambiente verificado com sucesso.")
            else:
                st.error("Falha na verificação do ambiente.")

        if st.button("Preparar estado inicial", use_container_width=True):
            returncode, output = run_and_store(
                "bootstrap_log",
                "python3 integrated-poc/scripts/02_bootstrap_onchain_state.py",
            )

            if returncode == 0:
                st.success("Estado inicial registrado na blockchain.")
            else:
                st.error("Falha no bootstrap on-chain.")

    with col2:
        st.subheader("2. Solicitação")

        if st.button("Criar solicitação de acesso", use_container_width=True):
            returncode, output = run_and_store(
                "request_access_log",
                "python3 integrated-poc/scripts/03_request_access.py",
            )

            request_id = extract_request_id_from_log(output)

            if request_id:
                st.session_state["last_request_id"] = request_id
                st.success(f"Solicitação registrada. Request ID: {request_id}")
            else:
                st.warning(
                    "Solicitação executada, mas o Request ID não foi identificado automaticamente."
                )

        if st.button("Processar solicitação de acesso", use_container_width=True):
            request_id = st.session_state.get("last_request_id")

            if not request_id:
                st.error("Nenhum Request ID disponível. Crie uma solicitação de acesso primeiro.")
            else:
                with st.spinner("Processando solicitação, gerando chave ABE e restaurando USK..."):
                    returncode, output = process_access_request(request_id)

                if returncode == 0:
                    st.success("Solicitação processada. Chave ABE protegida, recuperada e restaurada.")
                else:
                    st.error("Falha no processamento da solicitação.")

    with col3:
        st.subheader("3. Descriptografia")

        if st.button("Descriptografar payload", use_container_width=True):
            command = """
PYTHONPATH=integrated-poc/shared python3 - <<'PY'
from openabe_client import OpenABEClient

abe = OpenABEClient()
stdout, stderr = abe.decrypt_current_ciphertext()

print("STDOUT:")
print(stdout)

print("STDERR:")
print(stderr)
PY
"""

            returncode, output = run_and_store("decrypt_log", command)

            payload = extract_recovered_payload(output)
            st.session_state["last_payload"] = payload

            if returncode == 0 and payload:
                st.success("Payload descriptografado com sucesso.")
            elif returncode == 0:
                st.warning("Comando executado, mas o payload não foi identificado automaticamente.")
            else:
                st.error("Falha na descriptografia.")

    st.divider()

    st.subheader("Logs técnicos da sessão guiada")

    show_log("Verificação do ambiente", st.session_state["check_environment_log"])
    show_log("Bootstrap on-chain", st.session_state["bootstrap_log"])
    show_log("Solicitação de acesso", st.session_state["request_access_log"])
    show_log("Processamento da solicitação", st.session_state["process_access_log"], expanded=True)
    show_log("Descriptografia do payload", st.session_state["decrypt_log"], expanded=True)


with tab_full_demo:
    st.header("Demo completa reproduzível")

    st.markdown(
        """
Esta opção executa o fluxo completo por meio do script `run_full_demo.sh`.
Ao final, são gerados logs e um arquivo `demo_summary.json` em uma pasta com timestamp.

Esta aba mostra somente execuções feitas pelo botão **Executar demo completa**.
Execuções feitas pelo fluxo guiado aparecem na aba **Visão geral** e nos logs da sessão atual.
"""
    )

    if st.button("Executar demo completa", use_container_width=True):
        returncode, output = run_and_store(
            "full_demo_log",
            "./integrated-poc/scripts/run_full_demo.sh",
        )

        if returncode == 0:
            st.success("Demo completa executada com sucesso.")
        else:
            st.error("Falha na execução da demo completa.")

    show_log("Log da demo completa", st.session_state["full_demo_log"], expanded=True)

    latest_run, summary = get_latest_demo_summary()

    if latest_run:
        st.divider()
        st.subheader("Última demo completa registrada")
        st.caption(
            "Esta seção é atualizada apenas quando o script de demo completa é executado."
        )
        st.code(str(latest_run), language="text")

        if summary:
            guided_request_id = st.session_state.get("last_request_id") or "-"
            demo_request_id = summary.get("request_id", "-")

            if guided_request_id != "-" and str(guided_request_id) != str(demo_request_id):
                st.info(
                    f"O fluxo guiado mais recente usa Request ID {guided_request_id}, "
                    f"mas a última demo completa registrada usa Request ID {demo_request_id}. "
                    "Isso indica apenas que são execuções diferentes."
                )

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Request ID da demo", demo_request_id)

            with col2:
                st.metric("Chain ID", summary.get("chain_id", "-"))

            with col3:
                st.metric(
                    "Hash válido",
                    "Sim" if summary.get("key_hash_valid") else "Não",
                )

            with col4:
                st.metric(
                    "Decrypt",
                    "Sucesso" if summary.get("decryption_success") else "Falha",
                )

            st.subheader("Resumo da execução")
            st.json(summary)

            if summary.get("recovered_payload"):
                st.subheader("Payload recuperado na demo completa")
                st.json(summary.get("recovered_payload"))

        else:
            st.info("A última pasta de demo não possui um demo_summary.json válido.")
    else:
        st.info("Nenhuma demo completa registrada ainda.")


with tab_evidence:
    st.header("Evidências")

    st.markdown(
        """
Esta aba lista os arquivos gerados pela última execução da demo completa.
As execuções do fluxo guiado são exibidas nos logs da sessão, mas não geram
automaticamente uma pasta consolidada de evidências.
"""
    )

    latest_run = get_latest_demo_run()

    if not latest_run:
        st.info("Nenhuma pasta de evidência encontrada. Execute a demo completa primeiro.")
    else:
        st.markdown(f"Última pasta de evidências da demo completa: `{latest_run}`")

        evidence_files = sorted([item for item in latest_run.iterdir() if item.is_file()])

        selected_file = st.selectbox(
            "Arquivo de evidência",
            evidence_files,
            format_func=lambda path: path.name,
        )

        if selected_file:
            content = read_file(selected_file)

            st.subheader(selected_file.name)

            if selected_file.suffix == ".json":
                try:
                    st.json(json.loads(content))
                except Exception:
                    st.code(content, language="json")
            elif selected_file.suffix == ".csv":
                st.code(content, language="csv")
            else:
                st.code(content, language="text")


with tab_explanation:
    st.header("Explicação técnica")

    st.markdown(
        """
### Objetivo da interface

A interface foi criada para melhorar a reprodutibilidade e a demonstração da PoC.
Ela permite executar o fluxo de forma guiada, consultar logs e visualizar evidências
sem depender exclusivamente de comandos manuais no terminal.

### Diferença entre fluxo guiado e demo completa

A interface possui dois modos de execução. O **fluxo guiado** permite demonstrar
as etapas individualmente durante a explicação técnica. A **demo completa** executa
o fluxo integral por meio de um script automatizado e gera uma pasta de evidências
com logs e resumo JSON.

Por isso, os identificadores de solicitação podem ser diferentes entre os dois modos.
Eles representam execuções distintas da PoC.

### Papel da blockchain

A blockchain registra dispositivos, políticas associadas a tópicos, atributos dos
consumidores, solicitações de acesso e grants de chaves protegidas.

### Papel da Attribute Authority

A Attribute Authority é uma entidade off-chain responsável por gerar a chave de
usuário OpenABE com base nos atributos registrados para o consumidor na blockchain.

Ela não realiza a decisão final de acesso ao dado cifrado. No modelo CP-ABE, essa
decisão ocorre durante a descriptografia: se a chave do consumidor contém atributos
compatíveis com a política do ciphertext, a descriptografia funciona; caso contrário,
falha.

### Papel do ECIES

A chave ABE gerada pela Attribute Authority é protegida com ECIES antes de ser
registrada no contrato. Com isso, a blockchain armazena a chave protegida e o hash
de integridade, mas não expõe a chave ABE em texto claro.

### Papel do OpenABE

O OpenABE é responsável pela imposição criptográfica da política de acesso. A
recuperação do dado original só ocorre se os atributos presentes na chave do
consumidor satisfizerem a política aplicada ao dado cifrado.
"""
    )

    st.subheader("Fluxo resumido")

    st.code(
        """
1. O consumidor possui atributos registrados na blockchain.
2. O dado IIoT é cifrado com uma política CP-ABE.
3. O consumidor registra uma solicitação de acesso on-chain.
4. A Attribute Authority consulta os atributos do consumidor na blockchain.
5. A Attribute Authority gera uma chave OpenABE com esses atributos.
6. A chave ABE é protegida com ECIES.
7. A chave protegida e seu hash são registrados na blockchain.
8. O consumidor recupera e descriptografa a chave protegida.
9. A USK é restaurada no ambiente OpenABE.
10. O consumidor tenta descriptografar o payload.
11. O OpenABE libera ou bloqueia a recuperação do dado conforme a política do ciphertext.
""",
        language="text",
    )