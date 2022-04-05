import os
os.environ['SISTEC_DOWNLOAD_CONFIG']               = '/srv/www/sistec_download/config'
os.environ['SISTEC_DOWNLOAD_APP']                  = '/srv/www/sistec_download/app'
os.environ['SISTEC_DOWNLOAD_PLANILHAS_PRESENCIAL'] = '/srv/www/sistec_q/SISTEC-PARA-IMPORTACAO'
os.environ['SISTEC_DOWNLOAD_PLANILHAS_EAD']        = '/srv/www/sistec_ead/SISTEC-PARA-IMPORTACAO'
os.environ['SISTEC_DOWNLOAD_PLANILHAS_FIC']        = '/srv/www/sistec_fic/SISTEC-PARA-IMPORTACAO'
os.environ['SISTEC_DOWNLOAD_COOKIES']              = '/srv/www/sistec_download/upload'
os.environ['SISTEC_DOWNLOAD_LOG']                  = '/srv/www/sistec_download/log'

import sys
sys.path.insert(0, '/srv/www/sistec_download/app')

from sistec_download import app as application
