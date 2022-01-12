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
level_debug = [True, False, False]
# CONFIG DEBUG: FIM

# CONFIG PLANILHAS: INICIO
download_dir = u'%s' % getenv('SISTEC_DOWNLOAD_PLANILHAS', default='../planilhas')
if not path.exists(download_dir):
    try:
        makedirs(download_dir)
    except PermissionError:
        if download_dir[0] == '/':
            print('Sem permissão de escrita no diretório de download de planilhas de cursos presenciais:\n%s' % download_dir)
        else:
            print('Sem permissão de escrita no diretório de download de planilhas de cursos presenciais:\n%s' % path.join(os.getcwd(), download_dir))
        os._exit(1)
file_temp_path = u'%s/temp.txt' % download_dir
try:
    file_temp = open(file_temp_path, 'w')
except PermissionError:
    if download_dir[0] == '/':
        print('Sem permissão de escrita no diretório de download de planilhas de cursos presenciais:\n%s' % download_dir)
    else:
        print('Sem permissão de escrita no diretório de download de planilhas de cursos presenciais:\n%s' % path.join(os.getcwd(), download_dir))
    os._exit(1)
file_temp.close()
os.remove(file_temp_path)
# CONFIG PLANILHAS: FIM

# CONFIG UPLOAD DIR: INICIO
upload_dir = u'%s/' % getenv('SISTEC_DOWNLOAD_COOKIES', default='../upload')
if not path.exists(upload_dir):
    try:
        makedirs(upload_dir)
    except PermissionError:
        if upload_dir[0] == '/':
            print('Sem permissão de escrita no diretório de upload:\n%s' % upload_dir)
        else:
            print('Sem permissão de escrita no diretório de upload:\n%s' % path.join(os.getcwd(), upload_dir))
        os._exit(1)
file_temp_path = u'%s/temp.txt' % upload_dir
try:
    file_temp = open(file_temp_path, 'w')
except PermissionError:
    if upload_dir[0] == '/':
        print('Sem permissão de escrita no diretório de upload:\n%s' % upload_dir)
    else:
        print('Sem permissão de escrita no diretório de upload:\n%s' % path.join(os.getcwd(), upload_dir))
    os._exit(1)
file_temp.close()
os.remove(file_temp_path)
# CONFIG UPLOAD DIR: FIM

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
    global campus_encoding, file_debug_path, level_debug, upload_dir, download_dir
    error = None
    if request.method == 'POST':

        # CONFIG FILE COOKIES: INICIO
        cookies = request.files['cookies_json']
        cookies_filename = upload_dir + secure_filename(cookies.filename)
        try:
            cookies.save(cookies_filename)
        except IsADirectoryError:
            return render_template('upload.html', error='ERRO: O arquivo cookies.json não foi informado !!!')
        # CONFIG FILE COOKIES: FIM

        # CONFIG FILE SISTEC: INICIO
        sistec = request.files['sistec_html']
        sistec_filename = upload_dir + secure_filename(sistec.filename)
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

        # REGISTRANDO INFORMAÇÕES DE SESSÃO: INÍCIO
        session['planilhas'] = []
        session['planilhas'].append(download_dir)
        session['planilhas'].append(campi)
        session['cookies'] = cookies
        session['file_debug_path'] = file_debug_path
        session['level_debug'] = level_debug
        session.modified = True
        # REGISTRANDO INFORMAÇÕES DE SESSÃO: FIM

        return redirect(url_for('download'))

    # o código abaixo é executado se o método request
    # foi GET ou se as informações são inválidas
    return render_template('upload.html', error=error)


# app download
@app.route('/download', methods=['POST', 'GET'])
def download():
    error = None
    if request.method == 'POST':
        # VERIFICANDO QUAIS CAMPUS TEM QUE BAIXAR
        for i in session['planilhas'][1].items():
            key = i[0]
            try:
                baixar = request.form['planilha_' + key + i[1][0]]
            except KeyError:
                baixar = False
            if baixar == '1':
                baixar = True
            else:
                baixar = False
            tupla = (i[1][0], i[1][1], i[1][2], baixar)
            session['planilhas'][1][key] = tupla
        session.modified = True
        # VERIFICA SE TEM PELO MENOS UM CAMPUS MARCADO
        total_falso = True
        for i in session['planilhas'][1].items():
            # se flag de baixar eh ativo
            if i[1][3]:
                total_falso = False
                break
        if total_falso:
            return render_template('download.html', planilhas=session['planilhas'], error = u'ERRO: É para escolher ao menos um Câmpus !!!')
        # VERIFICA SE TEM MAIS DE UM PERFIL ESCOLHIDO PARA O MESMO CAMPUS
        campus_list = []
        for i in session['planilhas'][1].items():
            tupla = (i[1][1], i[1][3])
            if tupla not in campus_list:
                campus_list.append(tupla)
            elif i[1][3]:
                return render_template('download.html', planilhas=session['planilhas'], error=u'ERRO: NÃO se deve escolher dois ou mais perfis de um mesmo Câmpus !!!')
        # BAIXAR PLANILHAS: INICIO
        download_dir = session['planilhas'][0]
        qtde_perfis = len(session['planilhas'][1])
        for i in session['planilhas'][1].items():
            baixar = i[1][3]
            if baixar:
                cookies = session['cookies']
                cod_campus = i[1][0]
                campus = i[1][1]
                perfil = re.sub(r' ', r'+', i[1][2])
                get_data_sistec(cod_campus, campus, perfil, download_dir, qtde_perfis, cookies, file_debug_path, level_debug)
        # BAIXAR PLANILHAS: FIM
        return redirect(url_for('planilhas'))
    return render_template('download.html', planilhas=session['planilhas'], error=error)


# app planilhas
@app.route('/planilhas')
def planilhas():
    global campus_encoding
    campi = {}
    campi['planilhas'] = []
    for i in session['planilhas'][1].items():
        # se flag de baixar eh ativo
        if i[1][3]:
            campi['planilhas'].append({'caption': i[1][1].decode(campus_encoding), 'href': url_for('download_csv', planilha=i[1][1].decode(campus_encoding))})
    return render_template('planilhas.html', campi=campi)


# app download planilhas
@app.route('/planilhas/<planilha>.csv')
def download_csv(planilha):
    def read_csv(planilha):
        filename = u'%s/%s.csv' % (getenv('SISTEC_DOWNLOAD_PLANILHAS', default='../planilhas'), planilha)
        # verifica se existe a planilha
        if not path.exists(filename):
            abort(404)
        # retorna o generator para cada linha
        with open(filename, 'rb') as filecsv:
            for line in filecsv:
                yield line
    return Response(read_csv(planilha=planilha), mimetype='text/csv')


