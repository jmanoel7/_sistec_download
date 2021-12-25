# sistec-download

Baixa as planilhas do SISTEC automaticamente para fins de cruzamento de dados com o Q-Acadêmico

1. [Instalação](#instalação)
2. [Como usar](#como-usar)
3. [Para testar](#para-testar)

## Instalação

Para a instalação tanto do lado do servidor (back-end), como do lado do cliente (front-end), leia [INSTALL.md](INSTALL.md)

## Como usar

Para saber como usar leia [HOW_TO_USE.md](HOW_TO_USE.md)

## Para testar

Seria bom realizar um teste em paralelo do sistema:

- Instalar em três contêineres distintos [docker](https://hub.docker.com/_/ubuntu) o back-end do sistema em máquinas ubuntu server 20.04 LTS

- Iniciar 3 Perfis distintos do Firefox (ou 3 pessoas distintas do Chrome), cada um conectado com um dos contêineres do item acima.

- Realizar em uma instância do navegador web o download de planilhas presenciais, em outro EaD, e noutro FIC, para todos os campi da instituição.
