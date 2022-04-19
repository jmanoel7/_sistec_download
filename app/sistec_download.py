# -*- coding: utf-8 -*-


import re
import os
from os import path, getenv, makedirs
from time import strftime
from flask import abort, Response, Flask, render_template, redirect, url_for, request, session
from werkzeug.utils import secure_filename
import json
from json.decoder import JSONDecodeError
from sistec_lib import get_data_sistec


# CONFIG GERAL: INICIO
campus_encoding = 'utf-8'
# CONFIG GERAL: FIM
# CONFIG DEBUG: INICIO
logDir = u'%s' % getenv('SISTEC_DOWNLOAD_LOG', default='../log')
if not path.exists(logDir):
    try:
        makedirs(logDir)
    except PermissionError:
        if logDir[0] == '/':
            print('Sem permissão de escrita no diretório de log:\n%s' % logDir)
        else:
            print('Sem permissão de escrita no diretório de log:\n%s' % path.join(os.getcwd(), logDir))
        os._exit(1)
file_debug_path = u'%s/sistec_download_%s.log' % (logDir, strftime('%Y-%m-%d'))
try:
    file_debug = open(file_debug_path, 'a')
except PermissionError:
    print('Sem permissão de escrita no arquivo de log:\n%s' % file_debug_path)
    os._exit(1)
file_debug.close()
level_debug = [True, True, False]
# CONFIG DEBUG: FIM
# CONFIG PLANILHAS PRESENCIAIS: INICIO
downPRE_Dir = u'%s' % getenv('SISTEC_DOWNLOAD_PLANILHAS_PRESENCIAL', default='../planilhas/presencial')
if not path.exists(downPRE_Dir):
    try:
        makedirs(downPRE_Dir)
    except PermissionError:
        if downPRE_Dir[0] == '/':
            print('Sem permissão de escrita no diretório de download de planilhas de cursos presenciais:\n%s' % downPRE_Dir)
        else:
            print('Sem permissão de escrita no diretório de download de planilhas de cursos presenciais:\n%s' % path.join(os.getcwd(), downPRE_Dir))
        os._exit(1)
file_temp_path = u'%s/temp.txt' % downPRE_Dir
try:
    file_temp = open(file_temp_path, 'w')
except PermissionError:
    if downPRE_Dir[0] == '/':
        print('Sem permissão de escrita no diretório de download de planilhas de cursos presenciais:\n%s' % downPRE_Dir)
    else:
        print('Sem permissão de escrita no diretório de download de planilhas de cursos presenciais:\n%s' % path.join(os.getcwd(), downPRE_Dir))
    os._exit(1)
file_temp.close()
os.remove(file_temp_path)
# CONFIG PLANILHAS PRESENCIAIS: FIM
# CONFIG PLANILHAS EAD: INICIO
downEAD_Dir = u'%s' % getenv('SISTEC_DOWNLOAD_PLANILHAS_EAD', default='../planilhas/ead')
if not path.exists(downEAD_Dir):
    try:
        makedirs(downEAD_Dir)
    except PermissionError:
        if downEAD_Dir[0] == '/':
            print('Sem permissão de escrita no diretório de download de planilhas de cursos EaD:\n%s' % downEAD_Dir)
        else:
            print('Sem permissão de escrita no diretório de download de planilhas de cursos EaD:\n%s' % path.join(os.getcwd(), downEAD_Dir))
        os._exit(1)
file_temp_path = u'%s/temp.txt' % downEAD_Dir
try:
    file_temp = open(file_temp_path, 'w')
except PermissionError:
    if downEAD_Dir[0] == '/':
        print('Sem permissão de escrita no diretório de download de planilhas de cursos EaD:\n%s' % downEAD_Dir)
    else:
        print('Sem permissão de escrita no diretório de download de planilhas de cursos EaD:\n%s' % path.join(os.getcwd(), downEAD_Dir))
    os._exit(1)
file_temp.close()
os.remove(file_temp_path)
# CONFIG PLANILHAS EAD: FIM
# CONFIG PLANILHAS FIC: INICIO
downFIC_Dir = u'%s' % getenv('SISTEC_DOWNLOAD_PLANILHAS_FIC', default='../planilhas/fic')
if not path.exists(downFIC_Dir):
    try:
        makedirs(downFIC_Dir)
    except PermissionError:
        if downFIC_Dir[0] == '/':
            print('Sem permissão de escrita no diretório de download de planilhas de cursos FIC:\n%s' % downFIC_Dir)
        else:
            print('Sem permissão de escrita no diretório de download de planilhas de cursos FIC:\n%s' % path.join(os.getcwd(), downFIC_Dir))
        os._exit(1)
file_temp_path = u'%s/temp.txt' % downFIC_Dir
try:
    file_temp = open(file_temp_path, 'w')
except PermissionError:
    if downFIC_Dir[0] == '/':
        print('Sem permissão de escrita no diretório de download de planilhas de cursos FIC:\n%s' % downFIC_Dir)
    else:
        print('Sem permissão de escrita no diretório de download de planilhas de cursos FIC:\n%s' % path.join(os.getcwd(), downFIC_Dir))
    os._exit(1)
file_temp.close()
os.remove(file_temp_path)
# CONFIG PLANILHAS FIC: FIM
# CONFIG UPLOAD DIR: INICIO
uploadDir = u'%s/' % getenv('SISTEC_DOWNLOAD_COOKIES', default='../upload')
if not path.exists(uploadDir):
    try:
        makedirs(uploadDir)
    except PermissionError:
        if uploadDir[0] == '/':
            print('Sem permissão de escrita no diretório de upload:\n%s' % uploadDir)
        else:
            print('Sem permissão de escrita no diretório de upload:\n%s' % path.join(os.getcwd(), uploadDir))
        os._exit(1)
file_temp_path = u'%s/temp.txt' % uploadDir
try:
    file_temp = open(file_temp_path, 'w')
except PermissionError:
    if uploadDir[0] == '/':
        print('Sem permissão de escrita no diretório de upload:\n%s' % uploadDir)
    else:
        print('Sem permissão de escrita no diretório de upload:\n%s' % path.join(os.getcwd(), uploadDir))
    os._exit(1)
file_temp.close()
os.remove(file_temp_path)
# CONFIG UPLOAD DIR: FIM
# CONFIG TIPOS DE CURSOS: INICIO
# Presencial, EaD, FIC
tipos = [True, True, True]
downloadsDir = [downPRE_Dir, downEAD_Dir, downFIC_Dir]
# CONFIG TIPOS DE CURSOS: FIM
# CONFIG APP FLASK: INICIO
app = Flask(__name__)
app.secret_key = b'DTAT124154%*dtcl240580+='
# CONFIG APP FLASK: FIM


# app raiz
@app.route('/')
def index():
    return redirect(url_for('login'))


# app login
@app.route('/login', methods=['POST', 'GET'])
def login():
    global campus_encoding, file_debug_path, level_debug, uploadDir, tipos, downloadsDir
    error = None
    if request.method == 'POST':
        # CONFIG FILE COOKIES: INICIO
        cookies = request.files['cookies_json']
        cookies_filename = uploadDir + secure_filename(cookies.filename)
        try:
            cookies.save(cookies_filename)
        except IsADirectoryError:
            return render_template('upload.html', error='ERRO: O arquivo cookies.json não foi informado !!!')
        # CONFIG FILE COOKIES: FIM
        # CONFIG FILE SISTEC: INICIO
        sistec = request.files['sistec_html']
        sistec_filename = uploadDir + secure_filename(sistec.filename)
        try:
            sistec.save(sistec_filename)
        except IsADirectoryError:
            return render_template('upload.html', error='ERRO: O arquivo sistec.html não foi informado !!!')
        # CONFIG FILE SISTEC: FIM
        # CONFIG DADOS COOKIES: INICIO
        try:
            file_json = open(cookies_filename, 'r')
        except PermissionError:
            return render_template('upload.html', error='ERRO: Sem permissão de leitura do arquivo cookies.json !!!')
        try:
            cookies_data = json.load(file_json)
        except UnicodeDecodeError:
            return render_template('upload.html', error='ERRO: O arquivo cookies.json é inválido !!!')
        except JSONDecodeError:
            return render_template('upload.html', error='ERRO: O arquivo cookies.json é inválido !!!')
        file_json.close()
        cookie_phpsessid = None
        cookie_name = cookies_data[0]['name']
        if cookie_name == 'PHPSESSID':
            cookie_value = cookies_data[0]['value']
            cookie_phpsessid = cookie_name + '=' + cookie_value
        if not cookie_phpsessid:
            return render_template('upload.html', error='ERRO: O arquivo cookies.json não contêm os 2 cookies necessários: "TS01ea6fb6" e "PHPSESSID" !!!')
        cookie_noticias = "sistecNoticias=0"
        cookies = []
        cookies.append(cookie_phpsessid)
        cookies.append(cookie_noticias)
        # CONFIG DADOS COOKIES: FIM
        # CONFIG DADOS SISTEC: INICIO
        campi = {}
        try:
            with open(sistec_filename, mode='r', encoding='utf-8') as sistec_html:
                campus_list = []
                count = 0
                for line in sistec_html.readlines():
                    perfil = re.sub(r'^.*<option\s+title=[\"\']([A-Z\s]+)\s+-\s+INSTITUTO.+[\"\'].*$', r'\1', line)
                    if line == perfil:
                        continue
                    perfil = re.sub(r'\s+$', r'', perfil)
                    campus = u'CÂMPUS ' + re.sub(r'^.*<option\s+title=[\"\'].+\s+CAMPUS\s+([A-ZÁÃÂÉẼÊÍĨÎÓÕÔÚŨÛÇ\s]+)[\"\'].*$', r'\1', line)
                    campus = re.sub(r'\s+$', r'', campus)
                    campus = campus.encode(campus_encoding)
                    # AJUSTES PARA O IFG: INICIO
                    if campus == u'CÂMPUS ÁGUAS LINDAS DE GOIÁS'.encode(campus_encoding):
                        campus = u'CÂMPUS ÁGUAS LINDAS'.encode(campus_encoding)
                    if campus == u'CÂMPUS VALPARAÍSO DE GOIÁS'.encode(campus_encoding):
                        campus = u'CÂMPUS VALPARAÍSO'.encode(campus_encoding)
                    # AJUSTES PARA O IFG: FIM
                    if campus not in campus_list:
                        campus_list.append(campus)
                        baixar = True
                    else:
                        baixar = False
                    cod_campus = re.sub(r'^.*<option\s+title=[\"\'].+[\"\']\s+value=[\"\']([0-9]+)[\"\'].*$', r'\1', line)
                    cod_campus = re.sub(r'\s+$', r'', cod_campus)
                    tupla_campus = (cod_campus, campus, perfil, baixar)
                    if count < 10:
                        key = '0' + str(count)
                    else:
                        key = str(count)
                    campi[key] = tupla_campus
                    count = count + 1
        except PermissionError:
            return render_template('upload.html', error='ERRO: Sem permissão de leitura do arquivo sistec.html !!!')
        if len(campi) == 0:
            return render_template('upload.html', error='ERRO: O arquivo sistec.html não contêm nenhum câmpus !!!')
        # ORDENACAO DO DICIONARIO CAMPI
        campi = {key: value for key, value in sorted(campi.items(), key=lambda item: item[1][1])}
        # CONFIG DADOS SISTEC: FIM
        session['presencial'] = []
        session['presencial'].append(tipos[0])
        session['presencial'].append(downloadsDir[0])
        session['presencial'].append(campi)
        session['ead'] = []
        session['ead'].append(tipos[1])
        session['ead'].append(downloadsDir[1])
        session['ead'].append(campi)
        session['fic'] = []
        session['fic'].append(tipos[2])
        session['fic'].append(downloadsDir[2])
        session['fic'].append(campi)
        session['cookies'] = cookies
        session['file_debug_path'] = file_debug_path
        session['level_debug'] = level_debug
        session.modified = True
        return redirect(url_for('download'))
    # o código abaixo é executado se o método request
    # foi GET ou se as informações são inválidas
    return render_template('upload.html', error=error)


# app download
@app.route('/download', methods=['POST', 'GET'])
def download():
    error = None
    if request.method == 'POST':
        # Atualizar os dados de sessao referentes a cursos presenciais
        try:
            campi_presencial = request.form['campi_presencial']
        except KeyError:
            campi_presencial = False
        if campi_presencial == '1':
            campi_presencial = True
        else:
            campi_presencial = False
        session['presencial'][0] = campi_presencial
        for i in session['presencial'][2].items():
            key = i[0]
            try:
                baixar = request.form['pre_' + key + i[1][0]]
            except KeyError:
                baixar = False
            if baixar == '1':
                baixar = True
            else:
                baixar = False
            tupla = (i[1][0], i[1][1], i[1][2], baixar)
            session['presencial'][2][key] = tupla
        # Atualizar os dados de sessao referentes a cursos ead
        try:
            campi_ead = request.form['campi_ead']
        except KeyError:
            campi_ead = False
        if campi_ead == '1':
            campi_ead = True
        else:
            campi_ead = False
        session['ead'][0] = campi_ead
        for i in session['ead'][2].items():
            key = i[0]
            try:
                baixar = request.form['ead_' + key + i[1][0]]
            except KeyError:
                baixar = False
            if baixar == '1':
                baixar = True
            else:
                baixar = False
            tupla = (i[1][0], i[1][1], i[1][2], baixar)
            session['ead'][2][key] = tupla
        # Atualizar os dados de sessao referentes a cursos fic
        try:
            campi_fic = request.form['campi_fic']
        except KeyError:
            campi_fic = False
        if campi_fic == '1':
            campi_fic = True
        else:
            campi_fic = False
        session['fic'][0] = campi_fic
        for i in session['fic'][2].items():
            key = i[0]
            try:
                baixar = request.form['fic_' + key + i[1][0]]
            except KeyError:
                baixar = False
            if baixar == '1':
                baixar = True
            else:
                baixar = False
            tupla = (i[1][0], i[1][1], i[1][2], baixar)
            session['fic'][2][key] = tupla
        session.modified = True
        # VERIFICA SE TEM PELO MENOS UM TIPO DE CURSO MARCADO
        if (not session['presencial'][0]) and (not session['ead'][0]) and (not session['fic'][0]):
            return render_template('download.html', presencial=session['presencial'], ead=session['ead'], fic=session['fic'],
                error = u'ERRO: É para escolher ao menos um tipo de curso (presencial/ead/fic) !!!')
        # VERIFICA SE TEM PELO MENOS UM CAMPUS MARCADO
        total_falso = True
        for i in session['presencial'][2].items():
            # se flag de baixar eh ativo
            if i[1][3]:
                total_falso = False
                break
        if total_falso:
            for i in session['ead'][2].items():
                # se flag de baixar eh ativo
                if i[1][3]:
                    total_falso = False
                    break
        if total_falso:
            for i in session['fic'][2].items():
                # se flag de baixar eh ativo
                if i[1][3]:
                    total_falso = False
                    break
        if total_falso:
            return render_template('download.html', presencial=session['presencial'], ead=session['ead'], fic=session['fic'],
                error = u'ERRO: É para escolher ao menos um câmpus de um tipo de curso (presencial/ead/fic) !!!')
        # VERIFICA CURSOS PRESENCIAIS
        if session['presencial'][0]:
            campus_list = []
            for i in session['presencial'][2].items():
                tupla = (i[1][1], i[1][3])
                if tupla not in campus_list:
                    campus_list.append(tupla)
                elif i[1][3]:
                    return render_template('download.html', presencial=session['presencial'], ead=session['ead'], fic=session['fic'],
                        error=u'ERRO: NÃO se deve escolher dois ou mais perfis de um mesmo câmpus !!!')
            total_falso = True
            for i in session['presencial'][2].items():
                # se flag de baixar eh ativo
                if i[1][3]:
                    total_falso = False
                    break
            if total_falso:
                return render_template('download.html', presencial=session['presencial'], ead=session['ead'], fic=session['fic'],
                    error = u'ERRO: É para escolher ao menos um Câmpus para os cursos presenciais !!!')
        else:
            total_falso = True
            for i in session['presencial'][2].items():
                # se flag de baixar eh ativo
                if i[1][3]:
                    total_falso = False
                    break
            if not total_falso:
                return render_template('download.html', presencial=session['presencial'], ead=session['ead'], fic=session['fic'],
                    error = u'ERRO: Tem Câmpus marcado para os cursos presenciais, sendo que não está marcado a opção de cursos presenciais !!!')
        # VERIFICA CURSOS EAD
        if session['ead'][0]:
            campus_list = []
            for i in session['ead'][2].items():
                tupla = (i[1][1], i[1][3])
                if tupla not in campus_list:
                    campus_list.append(tupla)
                elif i[1][3]:
                    return render_template('download.html', presencial=session['presencial'], ead=session['ead'], fic=session['fic'],
                        error=u'ERRO: NÃO se deve escolher dois ou mais perfis de um mesmo câmpus !!!')
            total_falso = True
            for i in session['ead'][2].items():
                # se flag de baixar eh ativo
                if i[1][3]:
                    total_falso = False
                    break
            if total_falso:
                return render_template('download.html', presencial=session['presencial'], ead=session['ead'], fic=session['fic'],
                    error = u'ERRO: É para escolher ao menos um Câmpus para os cursos EaD !!!')
        else:
            total_falso = True
            for i in session['ead'][2].items():
                # se flag de baixar eh ativo
                if i[1][3]:
                    total_falso = False
                    break
            if not total_falso:
                return render_template('download.html', presencial=session['presencial'], ead=session['ead'], fic=session['fic'],
                    error = u'ERRO: Tem Câmpus marcado para os cursos EaD, sendo que não está marcado a opção de cursos EaD !!!')
        # VERIFICA CURSOS FIC
        if session['fic'][0]:
            campus_list = []
            for i in session['fic'][2].items():
                tupla = (i[1][1], i[1][3])
                if tupla not in campus_list:
                    campus_list.append(tupla)
                elif i[1][3]:
                    return render_template('download.html', presencial=session['presencial'], ead=session['ead'], fic=session['fic'],
                        error=u'ERRO: NÃO se deve escolher dois ou mais perfis de um mesmo câmpus !!!')
            total_falso = True
            for i in session['fic'][2].items():
                # se flag de baixar eh ativo
                if i[1][3]:
                    total_falso = False
                    break
            if total_falso:
                return render_template('download.html', presencial=session['presencial'], ead=session['ead'], fic=session['fic'],
                    error = u'ERRO: É para escolher ao menos um Câmpus para os cursos FIC !!!')
        else:
            total_falso = True
            for i in session['fic'][2].items():
                # se flag de baixar eh ativo
                if i[1][3]:
                    total_falso = False
                    break
            if not total_falso:
                return render_template('download.html', presencial=session['presencial'], ead=session['ead'], fic=session['fic'],
                    error = u'ERRO: Tem Câmpus marcado para os cursos FIC, sendo que não está marcado a opção de cursos FIC !!!')
        # CONFIGURAR VARIAVEIS PARA BAIXAR
        cookies = session['cookies']
        file_debug_path = session['file_debug_path']
        level_debug = session['level_debug']
        # BAIXAR PLANILHAS PRESENCIAIS: INICIO
        if session['presencial'][0]:
            tipos = [session['presencial'][0], False, False]
            downDir = session['presencial'][1]
            qtdPerfis = len(session['presencial'][2])
            for i in session['presencial'][2].items():
                baixar = i[1][3]
                if baixar:
                    cod_campus = i[1][0]
                    campus = i[1][1]
                    perfil = re.sub(r' ', r'+', i[1][2])
                    get_data_sistec(cod_campus, campus, perfil, tipos, downDir, qtdPerfis, cookies, file_debug_path, level_debug)
        # BAIXAR PLANILHAS PRESENCIAIS: FIM
        # BAIXAR PLANILHAS EAD: INICIO
        if session['ead'][0]:
            tipos = [False, session['ead'][0], False]
            downDir = session['ead'][1]
            qtdPerfis = len(session['ead'][2])
            for i in session['ead'][2].items():
                baixar = i[1][3]
                if baixar:
                    cod_campus = i[1][0]
                    campus = i[1][1]
                    perfil = re.sub(r' ', r'+', i[1][2])
                    get_data_sistec(cod_campus, campus, perfil, tipos, downDir, qtdPerfis, cookies, file_debug_path, level_debug)
        # BAIXAR PLANILHAS EAD: FIM
        # BAIXAR PLANILHAS FIC: INICIO
        if session['fic'][0]:
            tipos = [False, False, session['fic'][0]]
            downDir = session['fic'][1]
            qtdPerfis = len(session['fic'][2])
            for i in session['fic'][2].items():
                baixar = i[1][3]
                if baixar:
                    cod_campus = i[1][0]
                    campus = i[1][1]
                    perfil = re.sub(r' ', r'+', i[1][2])
                    get_data_sistec(cod_campus, campus, perfil, tipos, downDir, qtdPerfis, cookies, file_debug_path, level_debug)
        # BAIXAR PLANILHAS FIC: FIM
        return redirect(url_for('planilhas'))
    return render_template('download.html', presencial=session['presencial'], ead=session['ead'], fic=session['fic'], error=error)


# app planilhas
@app.route('/planilhas')
def planilhas():
    global campus_encoding
    campi = {}
    if session['presencial'][0]:
        campi['presencial'] = []
        for i in session['presencial'][2].items():
            # se flag de baixar eh ativo
            if i[1][3]:
                campi['presencial'].append({'caption': i[1][1].decode(campus_encoding), 'href': url_for('download_csv', tipo='presencial', planilha=i[1][1].decode(campus_encoding))})
    if session['ead'][0]:
        campi['ead'] = []
        for i in session['ead'][2].items():
            # se flag de baixar eh ativo
            if i[1][3]:
                campi['ead'].append({'caption': i[1][1].decode(campus_encoding), 'href': url_for('download_csv', tipo='ead', planilha=i[1][1].decode(campus_encoding))})
    if session['fic'][0]:
        campi['fic'] = []
        for i in session['fic'][2].items():
            # se flag de baixar eh ativo
            if i[1][3]:
                campi['fic'].append({'caption': i[1][1].decode(campus_encoding), 'href': url_for('download_csv', tipo='fic', planilha=i[1][1].decode(campus_encoding))})
    return render_template('planilhas.html', campi=campi)


# app download planilhas
@app.route('/planilhas/<tipo>/<planilha>.csv')
def download_csv(tipo, planilha):
    def read_csv(planilha, tipo):
        # verifica o tipo
        if tipo == 'presencial':
            filename = u'%s/%s.csv' % (getenv('SISTEC_DOWNLOAD_PLANILHAS_PRESENCIAL', default='../planilhas/' + tipo), planilha)
        elif tipo == 'ead':
            filename = u'%s/%s.csv' % (getenv('SISTEC_DOWNLOAD_PLANILHAS_EAD', default='../planilhas/' + tipo), planilha)
        elif tipo == 'fic':
            filename = u'%s/%s.csv' % (getenv('SISTEC_DOWNLOAD_PLANILHAS_FIC', default='../planilhas/' + tipo), planilha)
        else:
            abort(404)
        # verifica se existe a planilha
        if not path.exists(filename):
            abort(404)
        # retorna o generator para cada linha
        with open(filename, 'rb') as filecsv:
            for line in filecsv:
                yield line
    return Response(read_csv(planilha=planilha, tipo=tipo), mimetype='text/csv')
