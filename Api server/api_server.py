import json
import pymysql
import logging
import time
import sys

from flask import Flask, request
app = Flask(__name__) #create the Flask app

logging.basicConfig(filename='server.log', level=logging.DEBUG) #archivo de log
REINTENTOS_CONEXION_DB = 10

# To connect MySQL database
dbConectado = 0 # para manejar la conexion a la DB, 0 = desconectado
while dbConectado == 0:
    try:
        db = pymysql.connect(
            host=sys.argv[1],
            user=sys.argv[2],
            password = sys.argv[3],
            db=sys.argv[4]
        )
        dbConectado = 1
        logging.info(time.strftime("%c") + " DB conectada.")
    except:
        dbConectado = 0
        logging.error(time.strftime("%c") + " DB no conectada.")

@app.route('/serverInfo', methods = ['POST'])
def api_server():
    receivedInfo = json.loads(request.json)
    jsonProcess = json.dumps(receivedInfo["procesos"])
    jsonUsers = json.dumps(receivedInfo["users"])

    reintentos = 0 #conteo de reintentos
    #pregunto si se cayó la conexión de la DB y si no supero los reintentos automáticos
    while db.open == 0 and reintentos < REINTENTOS_CONEXION_DB:
        try:
            db.connect()
            logging.info(time.strftime("%c") + " Conexión reestablecida con la DB")
        except:
            reintentos+=1
            logging.error(time.strftime("%c") + " No se puede reestablecer conexion con la DB")

    try:
        cursor = db.cursor()
        #busco el ID del servidor para saber si ya existe y utilizarlo en los demas inserts, si no existe, lo inserto
        sql = "SELECT serverId from server WHERE serverName = %s AND serverProcessor = %s"
        values = (receivedInfo["nombreServidor"], receivedInfo["infoProcesador"])
        cursor.execute(sql, values)
        if cursor.rowcount == 0:
        #no existe servidor
            sql = "INSERT INTO server (serverName, serverProcessor) VALUES (%s, %s)"
            values = (receivedInfo["nombreServidor"], receivedInfo["infoProcesador"])
            cursor.execute(sql, values)
            db.commit()
            logging.info(time.strftime("%c") + " Servidor nuevo registrado: " + receivedInfo["nombreServidor"])
        else:
            logging.info(time.strftime("%c") + " Servidor existente:" + receivedInfo["nombreServidor"])
    except:
        logging.error(time.strftime("%c") + " No se pudo leer/registrar servidor " + receivedInfo["nombreServidor"])

    try:
        cursor = db.cursor()
        #busco el ID del servidor
        sql = "SELECT serverId from server WHERE serverName = %s AND serverProcessor = %s"
        values = (receivedInfo["nombreServidor"], receivedInfo["infoProcesador"])
        cursor.execute(sql, values)
        registro = cursor.fetchone()
        serverId = registro[0]

        #inserto en serverusersonline
        sql = "INSERT INTO serveronlineusers (serverId, users) VALUES (%s, %s)"
        values = (serverId, jsonUsers)
        cursor.execute(sql, values)

        #inserto en serverprocesses
        sql = "INSERT INTO serverprocesses (serverId, runningProcesses) VALUES (%s, %s)"
        values = (serverId, jsonProcess)
        cursor.execute(sql, values)

        # busco el ID del servidor en serveroperatingsystem
        sql = "SELECT serverId from serveroperatingsystem WHERE serverId = %s"
        values = (serverId)
        cursor.execute(sql, values)

        if cursor.rowcount == 0:
            #no existe servidor, entonces inserto
            sql = "INSERT INTO serveroperatingsystem (serverId, operatingSystemName, operatingSystemVersion) VALUES (%s, %s, %s)"
            values = (serverId, receivedInfo["soName"], receivedInfo["soVersion"])
            cursor.execute(sql, values)

        db.commit()
        logging.info(time.strftime("%c") + " Procesos corriendo, usuarios conectados y sistema operativo registrados para el servidor: "
                     + receivedInfo["nombreServidor"])

    except:
        logging.error(time.strftime("%c") + " No se pudo registrar procesos corriendo, usuarios conectados y sistema operativo para el servidor: "
                     + receivedInfo["nombreServidor"])

    return '1'

if __name__ == '__main__':
    #definir el host y el port en dónde estará escuchando el server
    if len(sys.argv) == 7:
        app.run(host=sys.argv[5], port=sys.argv[6])#corre en ip puerto deseado
    else:
        app.run()#corre en localhost