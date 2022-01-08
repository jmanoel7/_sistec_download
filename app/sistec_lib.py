# -*- coding: utf-8 -*-


import re
import json
import pycurl
from copy import copy
from os import path, fsync, getenv
from time import strftime
from io import BytesIO
from urllib.parse import urlencode

CON_TIMEOUT = 300
REQ_TIMEOUT = 3600
headers = {}
host_sistec = 'https://sistec.mec.gov.br'
encoding = 'iso-8859-1'
campus_encoding = 'utf-8'
log_dir = u'%s' % getenv('SISTEC_DOWNLOAD_LOG', default='../log')
pydbg_path = u'%s/pycurl_debug_%s.log' % (log_dir, strftime('%Y-%m-%d'))


def get_data_sistec(cod_campus, campus, perfil, tipos, download_dir, qtde_perfis, cookies, file_log_path=None, level_debug=[False, False, False]):
    global host_sistec, encoding, campus_encoding
    sucesso = False
    campus = campus.decode(campus_encoding)
    campus_csv = path.join(download_dir, campus + '.csv')
    file_csv = open(campus_csv, mode='w', encoding=encoding)
    sucesso, mensagem = write_csv(file_csv, campus, cod_campus, perfil, qtde_perfis, tipos, cookies, file_log_path, level_debug)
    file_csv.close()
    if sucesso:
        if level_debug[0]:
            with open(file_log_path, 'a') as file_log:
                file_log.write(u'%s O download da planilha do SISTEC (%s) foi efetuado com sucesso em:\t%s\n' % (
                    strftime('[%Y-%m-%d %H:%M:%S]'), campus.title(), campus_csv))
                file_log.flush()
                fsync(file_log.fileno())
        sucesso = True
    else:
        if level_debug[0]:
            with open(file_log_path, 'a') as file_log:
                file_log.write(u'%s Não foi possível salvar a planilha do SISTEC (%s) em:\t%s\t%s\n' % (
                    strftime('[%Y-%m-%d %H:%M:%S]'), campus.title(), campus_csv, mensagem))
                file_log.flush()
                fsync(file_log.fileno())
        sucesso = False
    return sucesso


def write_csv(file_csv, no_campus, co_campus, perfil, qtde_perfis, tipos, cookies, file_log_path = None, level_debug = [False, False, False]):
    u"""
    Percorre o sistec, pegando os dados dos alunos nos ciclos de matricula,
    do 'campus' e os salva no arquivo 'file_csv'.

    :file_csv:           arquivo csv onde salvar os dados do SISTEC
    :no_campus:          nome do campus no site do SISTEC
    :co_campus:          codigo do campus no site do SISTEC
    :perfil:             perfil do usuário no site do SISTEC
    :tipos:              tipos de cursos [Presencial, EaD, FIC]
    :cookies:            cookies da sessão aberta para acesso ao site do SISTEC
                         [phpsessid, jsessionid, zde, perfil, noticias]
    :http_header_common: cabecalho comum das requisicoes http ao site do SISTEC
    :returns:            Sucesso, Mensagem
    """
    global headers, host_sistec, encoding, CON_TIMEOUT, REQ_TIMEOUT

    url_alterar_perfil = 'https://sistec.mec.gov.br/index/selecionarinstituicao/alterar/perfil'
    url_index          = 'https://sistec.mec.gov.br/index/index'
    url_turmas         = 'https://sistec.mec.gov.br/gridciclo/turmas'
    url_ciclo_common   = 'https://sistec.mec.gov.br/gridciclo/listaralunosacao/periodo/-1/ciclo/'
    url_tempo_sessao   = 'https://sistec.mec.gov.br/tempo-sessao/get-tempo-sessao/'

    #header_cache          = 'Cache-Control: max-age=0'
    #header_dnt            = 'DNT: 1'
    header_connection     = 'Connection: keep-alive'
    header_upgrade        = 'Upgrade-Insecure-Requests: 1'
    header_content_type   = 'Content-type: application/x-www-form-urlencoded charset=' + encoding
    header_content_len    = 'Content-Length: 0'
    header_user_agent     = 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0'
    header_accept_text    = 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    header_accept_lang    = 'Accept-Language: pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3'
    header_accept_json    = 'Accept: application/json'
    header_accept_enc     = 'Accept-Encoding: gzip, deflate, br'
    header_xreq_xml       = 'X-Requested-With: XMLHttpRequest'
    header_xreq_json      = 'X-Request: JSON'
    header_sec_fetch_site = 'Sec-Fetch-Site: '
    header_sec_fetch_mode = 'Sec-Fetch-Mode: '
    header_sec_fetch_user = 'Sec-Fetch-User: '
    header_sec_fetch_dest = 'Sec-Fetch-Dest: '

    cookie_phpsessid = cookies[0]
    cookie_noticias = cookies[1]
    cookie_perfil = u'perfil_cookie=' + perfil
    cookie_usuario = u'co_usuario=' + co_campus

    turmas_json = path.join(getenv('SISTEC_DOWNLOAD_APP', default=path.curdir), '_turmas.json')
    alunos_json = path.join(getenv('SISTEC_DOWNLOAD_APP', default=path.curdir), '_alunos.json')

    # COLUNAS DO ARQUIVO CSV
    # 00: CO_ALUNO_IDENTIFICADO     # 01: CO_ALUNO                     # 02: NO_ALUNO                 # 03: NO_MAE_ALUNO       # 04: NO_NOME_SOCIAL
    # 05: NU_CPF                    # 06: DS_EMAIL                     # 07: CO_PESSOA_FISICA_ALUNO   # 08: DS_SENHA           # 09: CO_MATRICULA
    # 10: CO_CICLO_MATRICULA        # 11: CO_STATUS_CICLO_MATRICULA    # 12: CO_CURSO                 # 13: NU_CARGA_HORARIA   # 14: DT_DATA_INICIO
    # 15: DT_DATA_FIM_PREVISTO      # 16: CO_UNIDADE_ENSINO            # 17: CO_PERIODO_CADASTRO      # 18: NO_CICLO_MATRICULA # 19: ST_ATIVO
    # 20: CO_TIPO_OFERTA_CURSO      # 21: CO_TIPO_INSTITUICAO          # 22: CO_INSTITUICAO           # 23: CO_PORTFOLIO       # 24: CO_TIPO_NIVEL_OFERTA_CURSO
    # 25: CO_TIPO_PROGRAMA_CURSO    # 26: ST_CARGA                     # 27: DT_DATA_FINALIZADO       # 28: NU_VAGAS_OFERTADAS # 29: NU_TOTAL_INSCRITOS
    # 30: ST_ETEC                   # 31: CO_POLO                      # 32: UAB # 33: ST_PREVISTO    # 34: NU_VAGAS_PREVISTAS # 35: CO_CURSO_SUPERIOR_CORRELATO
    # 36: NU_CARGA_HORARIA_ESTAGIO  # 37: NO_ARQUIVO                   # 38: NO_CAMINHO_ARQUIVO       # 39: ST_ESTAGIO         # 40: ST_EXPERIMENTAL
    # 41: NO_STATUS_MATRICULA       # 42: CO_PESSOA_FISICA             # 43: NU_RG # 44: SG_SEXO      # 45: DT_NASCIMENTO      # 46: NO_PESSOA_FISICA
    # 47: CO_PESSOA                 # 48: CO_CARGO                     # 49: DS_ORGAO_EXPEDIDOR       # 50: SG_UF_ORG_EXPED
    # 51: DS_CARGO                  # 52: CO_UNIDADE_ENSINO_IMPORTACAO # 53: CO_MATRICULA_RESPONSAVEL # 54: NO_SOCIAL
    # USAREMOS AS SEGUINTES COLUNAS:
    # 02; 05; 10; 41; 18; 14; 16

    file_csv.write('NO_ALUNO;'
                   'NU_CPF;'
                   'CO_CICLO_MATRICULA;'
                   'NO_STATUS_MATRICULA;'
                   'NO_CICLO_MATRICULA;'
                   'DT_DATA_INICIO;'
                   'CO_UNIDADE_ENSINO'
                   '\n')

    file_csv.flush()
    fsync(file_csv.fileno())

    # =================
    # DOWNLOAD: ETAPA 1
    # =================
    """
    curl 'https://sistec.mec.gov.br/index/index'
        -X POST
        -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0'
        -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        -H 'Accept-Language: pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3'
        -H 'Accept-Encoding: gzip, deflate, br'
        -H 'Content-Type: application/x-www-form-urlencoded'
        -H 'Origin: https://sistec.mec.gov.br'
        -H 'Connection: keep-alive'
        -H 'Referer: https://sistec.mec.gov.br/index/selecionarinstituicao/alterar/perfil'
        -H 'Cookie: sistecNoticias=0; PHPSESSID=nhbshr78b5j39c8qd8s0nke51sc3rqme; PHPSESSID=nhbshr78b5j39c8qd8s0nke51sc3rqme; perfil_cookie=GESTOR+DA+UNIDADE+DE+ENSINO; co_usuario=1660653'
        -H 'Upgrade-Insecure-Requests: 1'
        -H 'Sec-Fetch-Dest: document'
        -H 'Sec-Fetch-Mode: navigate'
        -H 'Sec-Fetch-Site: same-origin'
        -H 'Sec-Fetch-User: ?1'
        --data-raw 'tipo=1660670&acao=&qtde_perfis=14'
    """

    if level_debug[0]:
        with open(file_log_path, 'a') as file_log:
            file_log.write(u'%s Acessando o peril do %s ...\n' % (strftime('[%Y-%m-%d %H:%M:%S]'), no_campus.title()))
            file_log.flush()
            fsync(file_log.fileno())
    headers = {}
    http_header = [
        header_user_agent,
        header_accept_text,
        header_accept_lang,
        header_accept_enc,
        header_content_type,
        header_connection,
        header_upgrade,
        header_sec_fetch_dest + 'document',
        header_sec_fetch_mode + 'navigate',
        header_sec_fetch_site + 'same-origin',
        header_sec_fetch_user + '?1',
        'Origin: ' + host_sistec,
        'Referer: ' + url_alterar_perfil,
        'Cookie: ' + cookie_phpsessid + '; ' + cookie_perfil + '; ' + cookie_noticias + '; ' + cookie_usuario
    ]
    http_header[-1] = http_header[-1].encode(encoding)
    http_header[-2] = http_header[-2].encode(encoding)
    http_header[-3] = http_header[-3].encode(encoding)
    post_data = {
        'tipo': co_campus,
        'acao': '',
        'qtdPerfis': str(qtde_perfis)
    }
    postfields = urlencode(post_data)
    buff = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url_index)
    c.setopt(c.SSL_VERIFYPEER, 1)
    c.setopt(c.SSL_VERIFYHOST, 2)
    c.setopt(c.TCP_NODELAY, 1)
    c.setopt(c.TCP_FASTOPEN, 1)
    c.setopt(c.CONNECTTIMEOUT, CON_TIMEOUT)
    c.setopt(c.TIMEOUT, REQ_TIMEOUT)
    # c.setopt(c.CAINFO, path.join(path.curdir, 'curl-ca-bundle.crt'))
    c.setopt(c.WRITEFUNCTION, buff.write)
    c.setopt(c.HTTPHEADER, http_header)
    c.setopt(c.HEADERFUNCTION, _pycurl_header)
    c.setopt(c.CUSTOMREQUEST, 'POST')
    c.setopt(c.POSTFIELDS, postfields)
    if level_debug[2]:
        c.setopt(c.VERBOSE, 1)
        c.setopt(c.DEBUGFUNCTION, _pycurl_debug)
    c.perform()
    c.close()
    if level_debug[1]:
        with open(file_log_path, 'a') as file_log:
            file_log.write(u'%s post_data:\t%s\n' % (strftime('[%Y-%m-%d %H:%M:%S]'), post_data))
            file_log.flush()
            fsync(file_log.fileno())

    lines = []
    pagina_ciclos = 1
    total_paginas_ciclos = '#'

    while True:
        # =================
        # DOWNLOAD: ETAPA 2
        # =================
        """
        curl 'https://sistec.mec.gov.br/tempo-sessao/get-tempo-sessao/'
            -X POST
            -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0'
            -H 'Accept: application/json'
            -H 'Accept-Language: pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3'
            -H 'Accept-Encoding: gzip, deflate, br'
            -H 'X-Requested-With: XMLHttpRequest'
            -H 'X-Request: JSON'
            -H 'Content-type: application/x-www-form-urlencoded; charset=utf-8'
            -H 'Content-Length: 0'
            -H 'Origin: https://sistec.mec.gov.br'
            -H 'Connection: keep-alive'
            -H 'Referer: https://sistec.mec.gov.br/index/index'
            -H 'Cookie: sistecNoticias=0; PHPSESSID=nhbshr78b5j39c8qd8s0nke51sc3rqme; PHPSESSID=nhbshr78b5j39c8qd8s0nke51sc3rqme; perfil_cookie=GESTOR+DA+UNIDADE+DE+ENSINO; co_usuario=1660653'
            -H 'Sec-Fetch-Dest: empty'
            -H 'Sec-Fetch-Mode: cors'
            -H 'Sec-Fetch-Site: same-origin'
        """
        if level_debug[0]:
            with open(file_log_path, 'a') as file_log:
                file_log.write(u'%s Tempo de sessão do %s ... ' % (strftime('[%Y-%m-%d %H:%M:%S]'), no_campus.title()))
                file_log.flush()
                fsync(file_log.fileno())
        headers = {}
        http_header = [
            header_user_agent,
            header_accept_json,
            header_accept_lang,
            header_accept_enc,
            header_xreq_xml,
            header_xreq_json,
            header_content_type,
            header_content_len,
            header_connection,
            header_sec_fetch_dest + 'empty',
            header_sec_fetch_mode + 'cors',
            header_sec_fetch_site + 'same-origin',
            'Origin: ' + host_sistec,
            'Referer: ' + url_index,
            'Cookie: ' + cookie_noticias + '; ' + cookie_phpsessid + '; ' + cookie_perfil + '; ' + cookie_usuario
        ]
        http_header[-1] = http_header[-1].encode(encoding)
        http_header[-2] = http_header[-2].encode(encoding)
        http_header[-3] = http_header[-3].encode(encoding)
        data_buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, url_tempo_sessao)
        c.setopt(c.SSL_VERIFYPEER, 1)
        c.setopt(c.SSL_VERIFYHOST, 2)
        c.setopt(c.TCP_NODELAY, 1)
        c.setopt(c.TCP_FASTOPEN, 1)
        c.setopt(c.CONNECTTIMEOUT, CON_TIMEOUT)
        c.setopt(c.TIMEOUT, REQ_TIMEOUT)
        # c.setopt(c.CAINFO, path.join(path.curdir, 'curl-ca-bundle.crt'))
        c.setopt(c.WRITEDATA, data_buffer)
        c.setopt(c.HTTPHEADER, http_header)
        c.setopt(c.HEADERFUNCTION, _pycurl_header)
        c.setopt(c.CUSTOMREQUEST, 'POST')
        if level_debug[2]:
            c.setopt(c.VERBOSE, 1)
            c.setopt(c.DEBUGFUNCTION, _pycurl_debug)
        c.perform()
        c.close()
        tempo_sessao = data_buffer.getvalue().decode(encoding)
        if level_debug[0]:
            with open(file_log_path, 'a') as file_log:
                file_log.write(u'%s\n' % tempo_sessao)
                file_log.flush()
                fsync(file_log.fileno())

        """
        curl 'https://sistec.mec.gov.br/gridciclo/turmas'
            -X POST
            -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0'
            -H 'Accept: application/json'
            -H 'Accept-Language: pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3'
            -H 'Accept-Encoding: gzip, deflate, br'
            -H 'X-Requested-With: XMLHttpRequest'
            -H 'X-Request: JSON'
            -H 'Content-type: application/x-www-form-urlencoded; charset=utf-8'
            -H 'Origin: https://sistec.mec.gov.br'
            -H 'Connection: keep-alive'
            -H 'Referer: https://sistec.mec.gov.br/index/index'
            -H 'Cookie: sistecNoticias=0; PHPSESSID=nhbshr78b5j39c8qd8s0nke51sc3rqme; PHPSESSID=nhbshr78b5j39c8qd8s0nke51sc3rqme; perfil_cookie=GESTOR+DA+UNIDADE+DE+ENSINO; co_usuario=1660653'
            -H 'Sec-Fetch-Dest: empty'
            -H 'Sec-Fetch-Mode: cors'
            -H 'Sec-Fetch-Site: same-origin'
            --data-raw 'pagina=1'

        pagina=1
        while (True):
            ...
            if pagina < totalPaginas:
                pagina = pagina + 1
                continue
            break
        """
        if level_debug[0]:
            with open(file_log_path, 'a') as file_log:
                file_log.write(u'%s Acessando a página %s/%s da lista de ciclos do %s ...\n' % (
                    strftime('[%Y-%m-%d %H:%M:%S]'), pagina_ciclos, total_paginas_ciclos, no_campus.title()))
                file_log.flush()
                fsync(file_log.fileno())
        headers = {}
        http_header = [
            header_user_agent,
            header_accept_json,
            header_accept_lang,
            header_accept_enc,
            header_xreq_xml,
            header_xreq_json,
            header_content_type,
            header_connection,
            header_sec_fetch_dest + 'empty',
            header_sec_fetch_mode + 'cors',
            header_sec_fetch_site + 'same-origin'
            'Origin: ' + host_sistec,
            'Referer: ' + url_index,
            'Cookie: ' + cookie_noticias + '; ' + cookie_phpsessid + '; ' + cookie_perfil + '; ' + cookie_usuario
        ]
        http_header[-1] = http_header[-1].encode(encoding)
        http_header[-2] = http_header[-2].encode(encoding)
        http_header[-3] = http_header[-3].encode(encoding)
        post_data = {'pagina': pagina_ciclos}
        postfields = urlencode(post_data)
        file_json = open(turmas_json, mode='wb')
        c = pycurl.Curl()
        c.setopt(c.URL, url_turmas)
        c.setopt(c.SSL_VERIFYPEER, 1)
        c.setopt(c.SSL_VERIFYHOST, 2)
        c.setopt(c.TCP_NODELAY, 1)
        c.setopt(c.TCP_FASTOPEN, 1)
        c.setopt(c.CONNECTTIMEOUT, CON_TIMEOUT)
        c.setopt(c.TIMEOUT, REQ_TIMEOUT)
        # c.setopt(c.CAINFO, path.join(path.curdir, 'curl-ca-bundle.crt'))
        c.setopt(c.WRITEDATA, file_json)
        c.setopt(c.HTTPHEADER, http_header)
        c.setopt(c.HEADERFUNCTION, _pycurl_header)
        c.setopt(c.CUSTOMREQUEST, 'POST')
        c.setopt(c.POSTFIELDS, postfields)
        if level_debug[2]:
            c.setopt(c.VERBOSE, 1)
            c.setopt(c.DEBUGFUNCTION, _pycurl_debug)
        c.perform()
        c.close()
        file_json.close()
        file_json_r = open(turmas_json, mode='rb+')
        limpa_arquivo(file_json_r)
        turmas_data = json.load(file_json_r)
        file_json_r.close()
        if level_debug[1]:
            with open(file_log_path, 'a') as file_log:
                file_log.write(u'%s turmas_data:\t%s\n' % (
                    strftime('[%Y-%m-%d %H:%M:%S]'), turmas_data))
                file_log.flush()
                fsync(file_log.fileno())

        try:
            ciclos = turmas_data['dados']
        except Exception as erro:
            return (False, u"%s" % erro)

        for i in range(len(ciclos)):

            # PEGA O TIPO DE CURSO:
            tipo_curso = ciclos[i]['Tipo do Curso']

            # VERIFICA SE CURSO EH DO TIPO FIC:
            re_fic = re.compile(u'^.*FORMA[CÇ][AÃ]O\s*(INICIAL|CONTINUADA).*$')
            match_fic = re_fic.search(tipo_curso)

            # VERIFICA SE CURSO EH DO TIPO MULHERES MIL:
            re_mm = re.compile(u'^.*MULHERES\s*MIL.*$')
            match_mm = re_mm.search(tipo_curso)

            if match_fic or match_mm:
                continue

            # PEGA O CODIGO DA UNIDADE DE ENSINO:
            co_unidade_ensino = ciclos[i]['Alunos']['eventos']['click']
            match = re.search(r'^.*\"instituicao\":(\d+).*$', co_unidade_ensino)
            if not match:
                return (False, u"não foi possível determinar o código da unidade de ensino:\t%s" % co_unidade_ensino)
            co_unidade_ensino = match.group(1)
            if level_debug[1]:
                with open(file_log_path, 'a') as file_log:
                    file_log.write(u'%s co_unidade_ensino:\t%s\n' % (
                        strftime('[%Y-%m-%d %H:%M:%S]'), co_unidade_ensino))
                    file_log.flush()
                    fsync(file_log.fileno())

            # PEGA O CODIGO DO CICLO DE MATRICULA:
            co_ciclo_matricula = ciclos[i]['Alunos']['id']
            match = re.search(r'^.*acao_(\d+).*$', co_ciclo_matricula)
            if not match:
                return (False, u"não foi possível determinar o código do ciclo:\t%s" % co_ciclo_matricula)
            co_ciclo_matricula = match.group(1)
            if level_debug[1]:
                with open(file_log_path, 'a') as file_log:
                    file_log.write(u'%s co_ciclo_matricula:\t%s\n' % (
                        strftime('[%Y-%m-%d %H:%M:%S]'), co_ciclo_matricula))
                    file_log.flush()
                    fsync(file_log.fileno())

            # PEGA O PERIODO DO CICLO:
            periodo_ciclo = ciclos[i]['Período do Ciclo']
            if level_debug[1]:
                with open(file_log_path, 'a') as file_log:
                    file_log.write(u'%s periodo_ciclo:\t%s\n' % (
                        strftime('[%Y-%m-%d %H:%M:%S]'), periodo_ciclo))
                    file_log.flush()
                    fsync(file_log.fileno())

            # PEGA A DATA DO INICO:
            match = re.search(r'^.*(\d{2}/\d{2}/\d{4}).*$', periodo_ciclo)
            if not match:
                return (False, u"não foi possível determinar a data do início:\t%s" % periodo_ciclo)
            dt_data_inicio = match.group(1).strip()
            if level_debug[1]:
                with open(file_log_path, 'a') as file_log:
                    file_log.write(u'%s dt_data_inicio:\t%s\n' % (
                        strftime('[%Y-%m-%d %H:%M:%S]'), dt_data_inicio))
                    file_log.flush()
                    fsync(file_log.fileno())

            # PEGA O NOME DO CICLO DE MATRICULA:
            no_ciclo_matricula = ciclos[i]['Curso']
            no_ciclo_matricula = no_ciclo_matricula.strip()
            if level_debug[1]:
                with open(file_log_path, 'a') as file_log:
                    file_log.write(u'%s no_ciclo_matricula:\t%s\n' % (
                        strftime('[%Y-%m-%d %H:%M:%S]'), no_ciclo_matricula))
                    file_log.flush()
                    fsync(file_log.fileno())

            line_common = []
            line_common.append(co_ciclo_matricula + u';')
            line_common.append(no_ciclo_matricula + u';')
            line_common.append(dt_data_inicio + u';')
            line_common.append(co_unidade_ensino + u';')

            continue_alunos = 0
            pagina_alunos = 1
            while True:
                # =================
                # DOWNLOAD: ETAPA 3
                # =================
                """
                curl 'https://sistec.mec.gov.br/gridciclo/listaralunosacao/periodo//ciclo/2016341/coaluno/'
                    -X POST
                    -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0'
                    -H 'Accept: application/json'
                    -H 'Accept-Language: pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3'
                    -H 'Accept-Encoding: gzip, deflate, br'
                    -H 'X-Requested-With: XMLHttpRequest'
                    -H 'X-Request: JSON'
                    -H 'Content-type: application/x-www-form-urlencoded; charset=utf-8'
                    -H 'Origin: https://sistec.mec.gov.br'
                    -H 'Connection: keep-alive'
                    -H 'Referer: https://sistec.mec.gov.br/index/index'
                    -H 'Cookie: sistecNoticias=0; PHPSESSID=nhbshr78b5j39c8qd8s0nke51sc3rqme; PHPSESSID=nhbshr78b5j39c8qd8s0nke51sc3rqme; perfil_cookie=GESTOR+DA+UNIDADE+DE+ENSINO; co_usuario=1660653'
                    -H 'Sec-Fetch-Dest: empty'
                    -H 'Sec-Fetch-Mode: cors'
                    -H 'Sec-Fetch-Site: same-origin'
                    --data-raw 'registros=30&pagina=2'

                pagina=1
                while (True):
                    ...
                    if pagina < totalPaginas:
                        pagina = pagina + 1
                        continue
                    break
                """
                if level_debug[0]:
                    with open(file_log_path, 'a') as file_log:
                        file_log.write(u'%s Acessando a lista de alunos (%s) do ciclo:\t%s ...\n' % (
                            strftime('[%Y-%m-%d %H:%M:%S]'), no_campus.title(), no_ciclo_matricula.title()))
                        file_log.flush()
                        fsync(file_log.fileno())
                headers = {}
                url_ciclo = url_ciclo_common + co_ciclo_matricula + '/coaluno/'
                http_header = [
                    header_user_agent,
                    header_accept_json,
                    header_accept_lang,
                    header_accept_enc,
                    header_xreq_xml,
                    header_xreq_json,
                    header_content_type,
                    header_connection,
                    header_sec_fetch_dest + 'empty',
                    header_sec_fetch_mode + 'cors',
                    header_sec_fetch_site + 'same-origin',
                    'Origin: ' + host_sistec,
                    'Referer: ' + url_index,
                    'Cookie: ' + cookie_noticias + '; ' + cookie_phpsessid + '; ' + cookie_perfil + '; ' + cookie_usuario
                ]
                http_header[-1] = http_header[-1].encode(encoding)
                http_header[-2] = http_header[-2].encode(encoding)
                http_header[-3] = http_header[-3].encode(encoding)
                post_data = {'registros': 30, 'pagina': pagina_alunos}
                postfields = urlencode(post_data)
                file_json = open(alunos_json, mode='wb')
                c = pycurl.Curl()
                c.setopt(c.URL, url_ciclo)
                c.setopt(c.SSL_VERIFYPEER, 1)
                c.setopt(c.SSL_VERIFYHOST, 2)
                c.setopt(c.TCP_NODELAY, 1)
                c.setopt(c.TCP_FASTOPEN, 1)
                c.setopt(c.CONNECTTIMEOUT, CON_TIMEOUT)
                c.setopt(c.TIMEOUT, REQ_TIMEOUT)
                # c.setopt(c.CAINFO, path.join(path.curdir, 'curl-ca-bundle.crt'))
                c.setopt(c.WRITEDATA, file_json)
                c.setopt(c.HTTPHEADER, http_header)
                c.setopt(c.HEADERFUNCTION, _pycurl_header)
                c.setopt(c.CUSTOMREQUEST, 'POST')
                c.setopt(c.POSTFIELDS, postfields)
                if level_debug[2]:
                    c.setopt(c.VERBOSE, 1)
                    c.setopt(c.DEBUGFUNCTION, _pycurl_debug)
                c.perform()
                c.close()
                file_json.close()
                file_json_r = open(alunos_json, mode='rb+')
                limpa_arquivo(file_json_r)
                alunos_data = json.load(file_json_r)
                file_json_r.close()
                if level_debug[1]:
                    with open(file_log_path, 'a') as file_log:
                        file_log.write(u'%s url_ciclo:\t%s\n' % (
                            strftime('[%Y-%m-%d %H:%M:%S]'), url_ciclo))
                        file_log.write(u'%s http_header:\t%s\n' % (
                            strftime('[%Y-%m-%d %H:%M:%S]'), http_header))
                        file_log.write(u'%s post_data:\t%s\n' % (
                            strftime('[%Y-%m-%d %H:%M:%S]'), post_data))
                        file_log.write(u'%s alunos_data:\t%s\n' % (
                            strftime('[%Y-%m-%d %H:%M:%S]'), alunos_data))
                        file_log.flush()
                        fsync(file_log.fileno())

                try:
                    alunos = alunos_data['dados']
                except KeyError:
                    try:
                        total_paginas_alunos = alunos_data['totalPaginas']
                    except Exception as erro:
                        return (False, u"%s" % erro)
                    # print(pagina_alunos)
                    # print(total_paginas_alunos)
                    if pagina_alunos < total_paginas_alunos:
                        pagina_alunos = pagina_alunos + 1
                        continue_alunos = 1
                    else:
                        continue_alunos = 2

                if continue_alunos == 1:
                    continue_alunos = 0
                    continue # while alunos
                elif continue_alunos == 2:
                    continue_alunos = 0
                    break # while alunos

                for j in range(len(alunos)):

                    line = copy(line_common)

                    # PEGA O NOME DO ALUNO:
                    nome_aluno = alunos[j]['Aluno']
                    if level_debug[1]:
                        with open(file_log_path, 'a') as file_log:
                            file_log.write(u'%s nome_aluno:\t%s\n' % (
                                strftime('[%Y-%m-%d %H:%M:%S]'), nome_aluno))
                            file_log.flush()
                            fsync(file_log.fileno())
                    nome_aluno = nome_aluno.strip() + ';'
                    line.insert(0, nome_aluno)

                    # PEGA O CPF DO ALUNO:
                    cpf_aluno = alunos[j]['CPF']
                    if level_debug[1]:
                        with open(file_log_path, 'a') as file_log:
                            file_log.write(u'%s cpf_aluno:\t%s\n' % (
                                strftime('[%Y-%m-%d %H:%M:%S]'), cpf_aluno))
                            file_log.flush()
                            fsync(file_log.fileno())
                    cpf_aluno = cpf_aluno.strip() + ';'
                    line.insert(1, cpf_aluno)

                    # PEGA O STATUS DO ALUNO:
                    status_aluno = alunos[j]['Status']
                    if level_debug[1]:
                        with open(file_log_path, 'a') as file_log:
                            file_log.write(u'%s status_aluno:\t%s\n' % (
                                strftime('[%Y-%m-%d %H:%M:%S]'), status_aluno))
                            file_log.flush()
                            fsync(file_log.fileno())
                    status_aluno = status_aluno.strip()
                    line.insert(3, status_aluno)

                    # ADICIONA UMA LINHA DA PLANILHA NO ARRAY "lines":
                    line.append(u'\n')
                    line = u''.join(line)
                    line = limpa_linha(line, encoding)
                    lines.append(line)

                try:
                    total_paginas_alunos = alunos_data['totalPaginas']
                except Exception as erro:
                    return (False, u"%s" % erro)

                if pagina_alunos < total_paginas_alunos:
                    pagina_alunos = pagina_alunos + 1
                    continue  # while alunos
                break  # while alunos

        try:
            total_paginas_ciclos = turmas_data['totalPaginas']
        except Exception as erro:
            return (False, u"%s" % erro)

        if pagina_ciclos < total_paginas_ciclos:
            pagina_ciclos = pagina_ciclos + 1
            continue  # while ciclos
        break  # while ciclos

    if lines:
        file_csv.writelines(lines)
        file_csv.flush()
        fsync(file_csv.fileno())

    return (True, u'OK')


def limpa_linha(linha, encoding):
    try:
        linha = linha.encode(encoding)
    except UnicodeEncodeError:
        nova_linha = []
        for i in range(len(linha)):
            try:
                nova_linha.append(linha[i].encode(encoding))
            except UnicodeEncodeError:
                pass
        linha = u''.encode(encoding).join(nova_linha)
    linha = linha.decode('unicode-escape')
    linha = re.sub(r'\s+', u' ', linha)
    linha = re.sub(r'\s*;\s*', u';', linha)
    linha = re.sub(r'\s*$', u'', linha)
    linha = linha + u'\n'
    return linha


def limpa_arquivo(arquivo):
    while True:
        try:
            arquivo.seek(-1, path.os.SEEK_END)
        except OSError:
            arquivo.seek(0)
            return
        c = arquivo.read(1)
        if not c:
            arquivo.seek(0)
            return
        c = c.decode('unicode-escape')
        r = re.compile(u'[\s\"\'\)\]\}]')
        m = r.search(c)
        if m:
            arquivo.seek(0)
            return
        arquivo.seek(-1, path.os.SEEK_END)
        arquivo.truncate()
        arquivo.flush()


def _pycurl_debug(debug_type, debug_msg):
    global pydbg_path
    with open(pydbg_path, 'a') as pydbg_file:
        pydbg_file.write(u'%s DEBUG(%d):\t%s\n' % (strftime('[%Y-%m-%d %H:%M:%S]'), debug_type, debug_msg))
        pydbg_file.flush()
        fsync(pydbg_file.fileno())


def _pycurl_header(header_line):
    global headers, encoding
    header_line = header_line.decode(encoding)
    if ':' not in header_line:
        return
    name, value = header_line.split(':', 1)
    name = name.strip()
    name = name.lower()
    value = value.strip()
    if name == 'set-cookie':
        cookie, dados = value.split(';', 1)
        cookie = cookie.strip()
        cookie_name, cookie_value = cookie.split('=', 1)
        cookie_name = cookie_name.strip()
        cookie_value = cookie_value.strip()
    if name not in headers:
        headers[name] = value
    return