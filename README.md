# Sistema de Identificação e Autenticação Biométrica

## Como executar

1. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

2. Rode o sistema:
   ```
   python src/main.py
   ```

3. No menu:
   - **Opção 1** – cadastra um novo usuário. Você escolhe entre gerar uma
     digital simulada (para testes) ou informar o caminho de uma imagem
     real de impressão digital.
   - **Opção 2** – autentica um usuário: simula uma nova captura de um
     usuário já cadastrado (deve conceder acesso), simula um impostor
     (deve negar acesso), ou permite usar um arquivo de imagem real.
   - **Opção 3** – mostra o histórico de tentativas de acesso (log de
     auditoria).

## Estrutura do projeto

```
aps_biometria/
├── src/
│   ├── main.py              # interface de linha de comando (menu)
│   ├── gerador_digitais.py  # simulação/geração de imagens de digital
│   ├── biometria.py         # extração de características (ORB) e comparação
│   └── banco_dados.py       # persistência em SQLite (usuários, documentos, logs)
├── db/                      # banco de dados SQLite (criado automaticamente)
├── digitais/                # imagens de digitais cadastradas (criado automaticamente)
├── requirements.txt
└── README.md
```

## Como funciona o reconhecimento

O sistema usa o algoritmo **ORB** (OpenCV) para extrair pontos-chave e
descritores de cada imagem de digital, e compara duas digitais contando
quantos pontos-chave "casam" entre si (BFMatcher, distância de Hamming).
Se a proporção de pontos correspondentes ultrapassar um limiar
(`THRESHOLD_AUTENTICACAO` em `biometria.py`), o acesso é concedido.

## Sobre a simulação de digitais

Como não há leitor biométrico físico disponível, as digitais usadas nos
testes são geradas sinteticamente (`gerador_digitais.py`), produzindo
um padrão visual simplificado de cristas, inspirado em uma impressão digital. O
pipeline de extração e comparação de características é o mesmo que seria
usado com imagens reais — basta trocar a origem da imagem (opção
"informar caminho de um arquivo de imagem real" no menu) para usar fotos
reais de impressões digitais, caso disponíveis.

## Níveis de acesso

- **Nível 1** – informações públicas (acessível a todos os usuários cadastrados)
- **Nível 2** – restrito a diretores de divisão
- **Nível 3** – restrito ao Ministro do Meio Ambiente

Cada usuário cadastrado só visualiza documentos até o seu nível de acesso.


## Observações sobre a simulação

As imagens sintéticas são usadas apenas para demonstrar o fluxo de cadastro,
comparação e controle de acesso. Elas não constituem um banco biométrico real
e os resultados obtidos com elas não devem ser interpretados como métricas de
desempenho de um sistema AFIS ou de um leitor de impressões digitais real.

A semente usada na simulação é derivada de SHA-256, de forma estável entre
execuções do Python.
