import hashlib
import os
import sys
import cv2

sys.path.insert(0, os.path.dirname(__file__))

import banco_dados as db
import gerador_digitais as gerador
import biometria

PASTA_DIGITAIS = os.path.join(os.path.dirname(__file__), "..", "digitais")

def seed_por_nome(nome: str) -> int:
    nome_normalizado = nome.strip().casefold().encode("utf-8")
    digest = hashlib.sha256(nome_normalizado).digest()
    return int.from_bytes(digest[:8], "big") % 100000


def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")


def pausar():
    input("\nPressione ENTER para continuar...")


def ler_nivel_acesso() -> int:
    while True:
        entrada = input("Nível de acesso (1=Público, 2=Diretor, 3=Ministro): ").strip()
        if entrada in ("1", "2", "3"):
            return int(entrada)
        print("Erro: informe um nível válido (1, 2 ou 3).")


def menu_cadastrar():
    limpar_tela()
    print("=== CADASTRO DE NOVO USUÁRIO (ENROLLMENT BIOMÉTRICO) ===\n")

    nome = input("Nome completo: ").strip()
    if not nome:
        print("Erro: nome não pode ser vazio.")
        pausar()
        return

    nivel = ler_nivel_acesso()

    print("\nOrigem da imagem da digital:")
    print("  1. Simular captura (gera digital sintética para fins de teste)")
    print("  2. Informar caminho de um arquivo de imagem real")
    opcao = input("Escolha (1/2): ").strip()

    if opcao == "2":
        caminho_origem = input("Caminho do arquivo de imagem: ").strip()
        imagem = cv2.imread(caminho_origem, cv2.IMREAD_GRAYSCALE)
        if imagem is None:
            print(f"\nErro: não foi possível ler a imagem em '{caminho_origem}'. "
                  "Verifique o caminho e o formato do arquivo.")
            pausar()
            return
    else:
        seed = seed_por_nome(nome)
        imagem = gerador.gerar_digital(seed)
        print("\n(Digital sintética gerada para simulação de captura.)")

    try:
        biometria.extrair_caracteristicas(imagem)
    except biometria.DigitalInvalidaError as erro:
        print(f"\nErro ao processar a digital: {erro}")
        pausar()
        return

    os.makedirs(PASTA_DIGITAIS, exist_ok=True)
    nome_arquivo = f"{nome.lower().replace(' ', '_')}.png"
    caminho_salvo = os.path.join(PASTA_DIGITAIS, nome_arquivo)
    cv2.imwrite(caminho_salvo, imagem)

    usuario_id = db.cadastrar_usuario(nome, nivel, caminho_salvo)
    print(f"\nUsuário '{nome}' cadastrado com sucesso (ID {usuario_id}, "
          f"nível {nivel}).")
    pausar()


def _carregar_candidatos():
    candidatos = []
    for usuario_id, nome, nivel, caminho in db.listar_usuarios():
        imagem = cv2.imread(caminho, cv2.IMREAD_GRAYSCALE)
        if imagem is not None:
            candidatos.append((usuario_id, nome, imagem))
    return candidatos


def menu_autenticar():
    limpar_tela()
    print("=== AUTENTICAÇÃO BIOMÉTRICA ===\n")

    candidatos = _carregar_candidatos()
    if not candidatos:
        print("Nenhum usuário cadastrado ainda.")
        pausar()
        return

    print("Origem da imagem de tentativa de acesso:")
    print("  1. Simular nova captura de um usuário já cadastrado (teste de sucesso)")
    print("  2. Simular tentativa de um impostor (teste de rejeição)")
    print("  3. Informar caminho de um arquivo de imagem real")
    opcao = input("Escolha (1/2/3): ").strip()

    if opcao == "1":
        nome_teste = input("Nome do usuário cadastrado a simular: ").strip()
        seed = seed_por_nome(nome_teste)
        imagem_tentativa = gerador.simular_nova_captura(seed)
    elif opcao == "2":
        imagem_tentativa = gerador.gerar_digital_impostor(999999)
    else:
        caminho = input("Caminho do arquivo de imagem: ").strip()
        imagem_tentativa = cv2.imread(caminho, cv2.IMREAD_GRAYSCALE)
        if imagem_tentativa is None:
            print(f"\nErro: não foi possível ler a imagem em '{caminho}'.")
            db.registrar_log(None, None, False, None, "Falha na leitura do arquivo de imagem")
            pausar()
            return

    try:
        biometria.extrair_caracteristicas(imagem_tentativa)
    except biometria.DigitalInvalidaError as erro:
        print(f"\nErro: {erro}")
        db.registrar_log(None, None, False, None, str(erro))
        pausar()
        return

    resultado = biometria.autenticar(imagem_tentativa, candidatos)

    if resultado is None:
        print("\nACESSO NEGADO: digital não reconhecida (nenhum usuário "
              "correspondente encontrado acima do limiar de similaridade).")
        db.registrar_log(None, None, False, None, "Digital não corresponde a nenhum usuário cadastrado")
        pausar()
        return

    usuario_id, nome, score = resultado
    nivel_usuario = [niv for i, _nome, niv, _caminho in db.listar_usuarios() if i == usuario_id][0]
    db.registrar_log(usuario_id, nome, True, score, "Autenticado com sucesso")

    print(f"\nACESSO CONCEDIDO: {nome} (nível {nivel_usuario}) "
          f"-- similaridade: {score:.2f}")

    documentos = db.buscar_documentos_por_nivel(nivel_usuario)
    print(f"\nDocumentos disponíveis para o nível {nivel_usuario}:\n")
    for titulo, conteudo, nivel_doc in documentos:
        print(f"[Nível {nivel_doc}] {titulo}")
        print(f"    {conteudo}\n")

    pausar()


def menu_logs():
    limpar_tela()
    print("=== LOGS DE ACESSO (últimas 20 tentativas) ===\n")
    logs = db.listar_logs()
    if not logs:
        print("Nenhum log registrado ainda.")
    for nome, sucesso, score, motivo, data_hora in logs:
        status = "SUCESSO" if sucesso else "FALHA"
        nome_exibido = nome or "(não identificado)"
        score_exibido = f"{score:.2f}" if score is not None else "-"
        print(f"[{data_hora}] {status} | {nome_exibido} | score={score_exibido} | {motivo}")
    pausar()


def menu_principal():
    db.inicializar_banco()
    while True:
        limpar_tela()
        print("=====================================================")
        print(" SISTEMA DE IDENTIFICAÇÃO E AUTENTICAÇÃO BIOMÉTRICA")
        print(" Ministério do Meio Ambiente (dados fictícios) - APS")
        print("=====================================================\n")
        print("1. Cadastrar usuário")
        print("2. Autenticar (login biométrico)")
        print("3. Ver logs de acesso")
        print("0. Sair")
        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "1":
            menu_cadastrar()
        elif opcao == "2":
            menu_autenticar()
        elif opcao == "3":
            menu_logs()
        elif opcao == "0":
            print("Encerrando o sistema...")
            break
        else:
            print("Opção inválida.")
            pausar()


if __name__ == "__main__":
    menu_principal()
