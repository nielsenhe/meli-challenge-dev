import platform
import time
import psutil
import json
import requests
import sys
import logging

POST_URL = sys.argv[1] #recibe por parametro el HOST:PORT, ejemplo py agente.py http://192.168.1.45:5000/serverInfo
logging.basicConfig(filename='agente.log', level=logging.DEBUG)#archivo de log
REINTENTOS_CONEXION_API = 10

while True:
    procs = {p.pid: p.info for p in psutil.process_iter(['name', 'username'])} #procesos corriendo con owner
    dictionary = {
        "nombreServidor" : platform.node(), #nombre servidor
        "infoProcesador" : platform.processor(), #info del procesador
        "procesos" : procs, #procesos corriendo con owner
        "users" : psutil.users(), #usuarios conectados
        "soVersion" : platform.version(), #version del sistema operativo
        "soName" : platform.system() #nombre del sistema operativo
    }
    information = json.dumps(dictionary) #preparo la informacion relevada a enviar

    estadoConexionApi = 0 #bandera para definir si pudo enviar o no el post request
    reintentosApi = 0 #contador de reintentos
    while estadoConexionApi == 0 and reintentosApi < REINTENTOS_CONEXION_API:
        try:
            requests.post(url=POST_URL, json=information)
            logging.info(time.strftime("%c") + " Datos de servidor enviados: " + platform.node())
            time.sleep(20) #permite relevar la informacion cada XXXX segundos
        except:
            # si no se puedo conectar a API, vuelve a intentar luego de XXXX segundos, en el caso de microcortes
            logging.error(time.strftime("%c") + " No se puede enviar datos de servidor: " + platform.node())
            reintentosApi+=1
            estadoConexionApi = 1
