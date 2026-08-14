import sqlite3
import os
from datetime import datetime

CAMINHO_BANCO = os.path.join(os.path.dirname(__file__), "..", "db", "sistema.db")


def conectar():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def inicializar_banco():
    # """Cria as tabelas do sistema, caso não existam, e popula documentos."""
    os.makedirs(os.path.dirname(CAMINHO_BANCO), exist_ok=True)
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            nivel_acesso INTEGER NOT NULL CHECK (nivel_acesso IN (1, 2, 3)),
            caminho_digital TEXT NOT NULL,
            data_cadastro TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nivel_minimo INTEGER NOT NULL CHECK (nivel_minimo IN (1, 2, 3)),
            titulo TEXT NOT NULL,
            conteudo TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs_acesso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            nome_identificado TEXT,
            sucesso INTEGER NOT NULL,
            score REAL,
            motivo TEXT,
            data_hora TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM documentos")
    if cursor.fetchone()[0] == 0:
        _popular_documentos_ficticios(cursor)

    conexao.commit()
    conexao.close()


def _popular_documentos_ficticios(cursor):
    documentos = [
        (1, "Relatório público de monitoramento ambiental",
         "Dados agregados e anonimizados sobre qualidade de rios e lençóis "
         "freáticos, disponíveis para consulta geral."),
        (1, "Boletim de conscientização sobre agrotóxicos",
         "Material educativo sobre o impacto do uso irregular de agrotóxicos."),
        (2, "Mapeamento de propriedades com irregularidades - Divisão Sul",
         "Lista de propriedades rurais sob investigação por uso de "
         "agrotóxicos proibidos na região sul, para uso interno dos "
         "diretores de divisão."),
        (2, "Relatório técnico de contaminação de lençóis freáticos",
         "Análise técnica detalhada de níveis de contaminação por região."),
        (3, "Dossiê estratégico nacional de propriedades irregulares",
         "Consolidado nacional, com nomes de proprietários e ações "
         "jurídicas em curso, de acesso exclusivo do Ministro."),
        (3, "Plano estratégico de fiscalização confidencial",
         "Plano de operações futuras de fiscalização, sigiloso."),
    ]
    cursor.executemany(
        "INSERT INTO documentos (nivel_minimo, titulo, conteudo) VALUES (?, ?, ?)",
        documentos,
    )


def cadastrar_usuario(nome: str, nivel_acesso: int, caminho_digital: str) -> int:
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "INSERT INTO usuarios (nome, nivel_acesso, caminho_digital, data_cadastro) "
        "VALUES (?, ?, ?, ?)",
        (nome, nivel_acesso, caminho_digital, datetime.now().isoformat()),
    )
    conexao.commit()
    usuario_id = cursor.lastrowid
    conexao.close()
    return usuario_id


def listar_usuarios():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome, nivel_acesso, caminho_digital FROM usuarios")
    resultado = cursor.fetchall()
    conexao.close()
    return resultado


def buscar_documentos_por_nivel(nivel_usuario: int):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT titulo, conteudo, nivel_minimo FROM documentos "
        "WHERE nivel_minimo <= ? ORDER BY nivel_minimo",
        (nivel_usuario,),
    )
    resultado = cursor.fetchall()
    conexao.close()
    return resultado


def registrar_log(usuario_id, nome_identificado, sucesso: bool, score, motivo: str):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "INSERT INTO logs_acesso (usuario_id, nome_identificado, sucesso, "
        "score, motivo, data_hora) VALUES (?, ?, ?, ?, ?, ?)",
        (usuario_id, nome_identificado, int(sucesso), score, motivo,
         datetime.now().isoformat()),
    )
    conexao.commit()
    conexao.close()


def listar_logs(limite: int = 20):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT nome_identificado, sucesso, score, motivo, data_hora "
        "FROM logs_acesso ORDER BY id DESC LIMIT ?",
        (limite,),
    )
    resultado = cursor.fetchall()
    conexao.close()
    return resultado
