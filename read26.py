#!/usr/bin/python
#-*- coding: utf-8 -*-
from datetime import datetime
from datetime import date
from imutils.video import VideoStream
from pyzbar import pyzbar
import RPi.GPIO as GPIO
import MFRC522
import smbus
import time
import datetime
import hexdump
import MySQLdb
import threading 
from threading import Thread
import binascii
import hashlib
#import subprocess
#################################################VARIABLES#################################################
##Bloc1
B1S4=4
B1S5=5
B1S6=6
##Bloc2
B2S8=8
##Bloc3
B3S12=12
############################################################################################################
bOkString="Debut"
global continue_reading
continue_reading=False

keyA_Prive = [0x59,0x61,0x50,0x6F,0x54,0x74]
##caractéristique
CREDIT_TOTAL = 0
CONSO_JOUR = 0
CONSO_TOTAL = 0
NBR_SEAUX_MAX = 0
Solde=0
GCP_CLIENT_CODE=""
GCP_CODE=""
##LED
GPIO_LEDR = 36
GPIO_LEDV = 32
time_sleep_led=3
LAST_MSG = "" ## Message qui sera affiché avec RETIRER CARTE

# carte détectée (pour boucler tant que la carte n'a pas été retirée
Card_Insert = 0

# relais
GPIO_relais = 40# le relais est branche sur la pin 40 / GPIO21
GPIO.setmode(GPIO.BOARD) # comme la librairie MFRC522
GPIO.setwarnings(False)
GPIO.setup(GPIO_relais, GPIO.OUT)# Define some device parameters
GPIO.output(GPIO_relais, True) # éteindre relais
GPIO.setup(GPIO_LEDV, GPIO.OUT)
GPIO.setup(GPIO_LEDR, GPIO.OUT)

#################################################FONCTIONS#################################################
def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off 
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)

def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = the data
  # mode = 1 for data
  #        0 for command

  bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
  bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

  # High bits
  bus.write_byte(I2C_ADDR, bits_high)
  lcd_toggle_enable(bits_high)

  # Low bits
  bus.write_byte(I2C_ADDR, bits_low)
  lcd_toggle_enable(bits_low)

def lcd_toggle_enable(bits):
  # Toggle enable
  time.sleep(E_DELAY)
  bus.write_byte(I2C_ADDR, (bits | ENABLE))
  time.sleep(E_PULSE)
  bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
  time.sleep(E_DELAY)

def lcd_string(message,line):
  # Send string to display
  message = message.ljust(LCD_WIDTH," ")
  lcd_byte(line, LCD_CMD)
  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)
    
def msg(L1,L2):
	lcd_string(L1,LCD_LINE_1)
	lcd_string(L2,LCD_LINE_2)
	
I2C_ADDR  = 0x27
#I2C_ADDR  = 0x77# I2C device address, if any error, change this address to 0x3f
LCD_WIDTH = 16   # Maximum characters per line


#LCD 
# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

LCD_BACKLIGHT  = 0x08  # On
#LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

bus = smbus.SMBus(1)
lcd_init()
lcd_byte(0x01,LCD_CMD)

######################################################################################################################
def turnOn(pin):
    GPIO.output(pin,True)
    time.sleep(time_sleep_led)
    GPIO.output(pin,False)
    
def LED_Blink(Kel_led):
    iLed = threading.local()
    iLed.i = 0
    #GPIO.setmode(GPIO.BOARD)
    #GPIO.setwarnings(False)
    GPIO.setup(Kel_led, GPIO.OUT)
    while (iLed.i <= 15):
        GPIO.output(Kel_led, True)
        time.sleep(0.1)   
        GPIO.output(Kel_led, False)
        time.sleep(0.1)
        iLed.i = iLed.i + 1
def declencherelay():
    GPIO.output(GPIO_relais, False)
    # GPIO.output(GPIO_relais, True)
    time.sleep(2)#attend 2 secondes sans rien faire
    # GPIO.output(GPIO_relais, False)
    GPIO.output(GPIO_relais, True)
           
def h2str(entree):
    sortie=str(chr(entree))
    return sortie

def recup_date_val(dlv):
    Date_TEMP=""
    Date_TEMP_OUT=""	
    c= 1
    while (c<9):
        if(dlv[c]!=0):
            try:
                Date_TEMP=str(chr(dlv[c]))
                Date_TEMP_OUT=Date_TEMP_OUT+Date_TEMP
            except :
                print(" Contenu Illisible")
        c+=1
    return Date_TEMP_OUT

def read_card(backData):
    Datatemp = ""
    c =0
    while (c<16):
        if(backData[c]!=0):
            try:
                Datatemp=Datatemp+h2str(backData[c])
            except:
                print(" Contenu Illisible")
        c=c+1
    #print("\n")
    return Datatemp

def getdata(backData):
    
    GCP_CLIENT_CODE=h2str(backData[12])+h2str(backData[13])+h2str(backData[14])+h2str(backData[15])
    
    return h2str(backData[0]),recup_date_val(backData),int(backData[9])*256+int(backData[10]),backData[11],GCP_CLIENT_CODE

def Date_Comparison(DATE_VALID,DATE_DAY):
    global LAST_MSG
    if DATE_VALID >= DATE_DAY:
        bOkString="carte est à jour"
        bOK=True
    elif DATE_CARD_VALID < DATE_TODAY:
        t5 = threading.Thread(name='t5',target=turnOn, args=(GPIO_LEDR,)).start()
        DATE_expire=DATE_CARD_VALID[6]+DATE_CARD_VALID[7]+"-"+DATE_CARD_VALID[4]+DATE_CARD_VALID[5]+"-"+DATE_CARD_VALID[0]+DATE_CARD_VALID[1]+DATE_CARD_VALID[2]+DATE_CARD_VALID[3]
        msg("CARTE EXPIREE","      "+str(DATE_expire))
        LAST_MSG="EXP "+str(DATE_expire)
        time.sleep(1.5)
        msg("ADRESSEZ-VOUS","AU GUICHET")
        time.sleep(1.5)
        msg("CARTE EXPIREE","      "+str(DATE_expire))
        time.sleep(1.5)
        msg("ADRESSEZ-VOUS","AU GUICHET")
        time.sleep(1.5)
        bOkString="CARTE EXPIREE"
        bOK=False
        
    return bOK,bOkString

def CREDIT_Comparison(CREDIT_T,CONSO_T):
    global LAST_MSG
    if(CREDIT_T> CONSO_T):
        #bOkString="Crédit Cumulé"
        bOkString="Crédit Cumulé non-atteint"
        msg("LECTURE CARTE","PATIENTEZ ...")
        time.sleep(0.5)
        bOK=True
    elif(CREDIT_T <= CONSO_T):
        t5 = threading.Thread(name='t5',target=turnOn, args=(GPIO_LEDR,)).start()
        msg("PLUS DE CREDIT ",str(CREDIT_T)+"/"+str(CONSO_T))
        time.sleep(1.5)
        msg("RECHARGER CARTE",str(CREDIT_T)+"/"+str(CONSO_T))
        time.sleep(1.5)
        LAST_MSG = "SOLDE 0/" + str(CREDIT_T)
        bOkString="CREDIT EPUISE : " + str(CREDIT_T)
        bOK=False
        
    return bOK,bOkString

def Seaux_Comparison(NBR_SEAUX,CONSO_J):
    global LAST_MSG
    if(NBR_SEAUX > CONSO_J):
        #bOkString="Nombre seaux authorise par jour non-atteint"
        bOK=True
        bOkString="recuperation des balles"
    elif(NBR_SEAUX<= CONSO_J):
        bOkString="Nombre seaux autorise par jour atteint"
        msg("MAX SEAUX JOURS","ATTEINT "+str(CONSO_J)+"/"+str(NBR_SEAUX))
        LAST_MSG = "MAX JOUR ! ("+str(NBR_SEAUX)+")"
        time.sleep(1)
        t3 = threading.Thread(name='t3',target=LED_Blink, args=(GPIO_LEDR,)).start()
        bOK=False
        
    return bOK,bOkString
############################################################################################################################################################
def insert_passage(GCP_UID, GCP_CARD_TYPE, GCP_NOM,GCP_PRENOM,GCP_CLUB,GCP_DATE_VALID,GCP_DATE_PASSAGE,GCP_CREDIT,GCP_CONSO,GCP_JOUR_MAX,GCP_JOUR_USED,GCP_CLIENT_CODE,GCP_NOTE):
    try:
        db = MySQLdb.connect("127.0.0.1", "yapo", "pipi", "rpi")
        curs=db.cursor()
        query="INSERT INTO GCP SET GCP_UID='%s', GCP_CARD_TYPE='%s', GCP_NOM='%s', GCP_PRENOM='%s', GCP_CLUB='%s', GCP_DATE_VALID='%s', GCP_DATE_PASSAGE='%s',GCP_CREDIT='%s',GCP_CONSO='%s',GCP_JOUR_MAX='%s',GCP_JOUR_USED='%s',GCP_CLIENT_CODE='%s', 	NOTE='%s'" % (GCP_UID, GCP_CARD_TYPE, GCP_NOM,GCP_PRENOM,GCP_CLUB,GCP_DATE_VALID,GCP_DATE_PASSAGE,GCP_CREDIT,GCP_CONSO,GCP_JOUR_MAX,GCP_JOUR_USED,GCP_CLIENT_CODE,GCP_NOTE)
        curs.execute(query)
        print("log a bien été ajouté !'")
        db.commit()
        db.close()
    except MySQLdb.Error as err:
        print("Exception while MYSQL Connection")
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
            db.close()
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
            db.close()
        else:
            print(err)
            db.close()

######################################################################################################################
def barcode_scan():
    # initialize the video stream and allow the camera sensor to warm up
    print("[INFO] starting video stream...")
    vs = VideoStream(usePiCamera=True).start()
    time.sleep(2.0)

    barcodeData=""
    old=""
    try:
        while True:
            frame = vs.read()
            barcodes = pyzbar.decode(frame)
##            
            for barcode in barcodes:
                barcodeData = barcode.data.decode("utf-8")
                print("Barcode",barcodeData)
                if old != barcodeData:
                    
                    old=barcodeData
                    barcodeDatahex=barcodeData.encode('utf-8')
                    hash_object = hashlib.md5(barcodeDatahex)
                    print("hex",barcodeDatahex)
                    print("Data en Hex() : ",barcodeDatahex.hex())
                    print("MD5 hashing code! ",hash_object.hexdigest())
                
                
                
                
    except KeyboardInterrupt:
        print("[INFO] cleaning up...")
        vs.stop()
######################################################################################################################
# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()
i=0

try:
    while True:
        w = threading.Thread(name='barcode_scan', target=barcode_scan).start()
        i=i+1
        stoday = datetime.datetime.today()
        DATE_TODAY=stoday.strftime("%Y%m%d")
        # Display Message
        lcd_string(stoday.strftime("%d-%m-%Y %H:%M"),LCD_LINE_1)
        lcd_string("Attente Carte",LCD_LINE_2)
        
        print("Attente Carte : ",i)
        # Scan for cards
        (bOK,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
        # If a card is found
        if bOK == MIFAREReader.MI_OK:
            bOkString="Carte detectee"
            print (bOkString)
        # Get the UID of the card
        (bOK,uid) = MIFAREReader.MFRC522_Anticoll()
        
        # If we have the UID, continue
        if bOK == MIFAREReader.MI_OK:
            # Mémoriser que l'on a détecté une carte
            Card_Insert = 1
            # Print UID
            # GCP_UID=str(uid[0])+str(uid[1])+str(uid[2])+str(uid[3])
            GCP_UID = '%02X' % uid[0] + ':%02X' % uid[1] + ':%02X' % uid[2] + ':%02X' % uid[3] + ':%02X' % uid[4]
            
            bOkString="UID de la carte: "
            print (bOkString,GCP_UID)
            
            # Select the scanned tag
            MIFAREReader.MFRC522_SelectTag(uid)
            
            # Authenticate with private key
            print("..............................BLOC 1.....................................")
            bOK = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, B1S4,keyA_Prive, uid)
            # Check if authenticated
            if(bOK == MIFAREReader.MI_OK):
                bOkString="authentification bloc 1 successfull"
                print(bOkString)
                try:
                    nomData= MIFAREReader.MFRC522_Read(B1S4)
                    GCP_NOM = read_card(nomData)
                except:
                    print("echec-lecture-secteur-",B1S4)
                    
                try:
                    prenomData = MIFAREReader.MFRC522_Read(B1S5)
                    GCP_PRENOM = read_card(prenomData)
                except:
                    print("echec-lecture-secteur-",B1S5)
                
                try:
                    societeData  = MIFAREReader.MFRC522_Read(B1S6)
                    GCP_CLUB = read_card(societeData)
                except:
                    print("echec-lecture-secteur-",B1S6)
            else:
                print("Error Authentification ",B1S4,"-Bloc 1")
                MIFAREReader.MFRC522_StopCrypto1()
                
            print("..............................BLOC 2.....................................")
            bOK = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, B2S8,keyA_Prive, uid)
            # Check if authenticated
            if(bOK == MIFAREReader.MI_OK):
                bOkString="authentification bloc 2 successfull"
                print(bOkString)
                try:
                    Data= MIFAREReader.MFRC522_Read(B2S8)
                    TYPE_CARD=(getdata(Data)[0])
                    DATE_CARD_VALID=(getdata(Data)[1])
                    CREDIT_TOTAL=(getdata(Data)[2])
                    NBR_SEAUX_MAX=(getdata(Data)[3])
                    GCP_CLIENT_CODE=(getdata(Data)[4])
                except:
                    print("echec-lecture-secteur-",B2S8)
            else:
                print("Error Authentification ",B2S8,"- Bloc 2")
                MIFAREReader.MFRC522_StopCrypto1()
  
            print("..............................BLOC 3.....................................")
            bOK = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, B3S12,keyA_Prive, uid)
            # Check if authenticated
            if(bOK == MIFAREReader.MI_OK):
                bOkString="authentification bloc 3 successfull"
                print(bOkString)
                try:
                    Data= MIFAREReader.MFRC522_Read(B3S12)
                    CARD=(getdata(Data)[0])
                    DATE_LAST_PASS=(getdata(Data)[1])
                    CONSO_TOTAL=(getdata(Data)[2])
                    CONSO_JOUR=(getdata(Data)[3])
                    GCP_CODE=(getdata(Data)[4])
                except:
                    print("echec-lecture-secteur-",B3S12)
                    
                if TYPE_CARD == "A":
                    print("\n")
                    print("BONJOUR ",GCP_NOM)
                    msg("BONJOUR ...",GCP_NOM)
                    time.sleep(2)
                else:
                    msg("CARTE","COMPTEUR")
                    time.sleep(2)
                #VERIFIER LA DATE  
                bOK,bOkString=Date_Comparison(DATE_CARD_VALID,DATE_TODAY)
                print("\n")
                if bOK == True:
                    print(bOkString)
                    #VERIFIER CREDIT
                    bOK,bOkString=CREDIT_Comparison(CREDIT_TOTAL,CONSO_TOTAL)
                    if bOK == True:
                        print(bOkString)
                        print("\n")
                        ###Passage
                        if(DATE_TODAY > DATE_LAST_PASS):
                            DATE_LAST_PASS = DATE_TODAY
                            CONSO_JOUR = 0
                        if(DATE_TODAY == DATE_LAST_PASS):
                            #VERIFIER LES SEAUX
                            bOK,bOkString=Seaux_Comparison(NBR_SEAUX_MAX,CONSO_JOUR)
                            if bOK == True:
                                print(bOkString)
                                print("Unités Consommées",CONSO_TOTAL,"\n")
                                print("Unités Consommées du jour:",CONSO_JOUR,"\n")
                                CONSO_JOUR = CONSO_JOUR+1
                                CONSO_TOTAL = CONSO_TOTAL+1
                                
                                Solde=(int(CREDIT_TOTAL)-int(CONSO_TOTAL))
                                #VERIFIER SOLDE
                                if Solde > 5:
                                    t4 = threading.Thread(name='t4',target=turnOn, args=(GPIO_LEDV,)).start()
                                if Solde > 0 and Solde <= 5:
                                    t2 = threading.Thread(name='t2',target=LED_Blink, args=(GPIO_LEDV,)).start()
                                
                                s = b"X" + DATE_TODAY.encode() + (CONSO_TOTAL).to_bytes(2, byteorder='big') + (CONSO_JOUR).to_bytes(1, byteorder='big') + b"YAPO"
                                
                                try:
                                    print("ECRITURE SUR LA CARTE...")
                                    bOK,StatusString=MIFAREReader.MFRC522_Write(B3S12,s)
                                    
                                    if bOK == 0:
                                        print(StatusString)
                                        insert_passage(GCP_UID,TYPE_CARD, GCP_NOM,GCP_PRENOM,GCP_CLUB,DATE_CARD_VALID,DATE_LAST_PASS,CREDIT_TOTAL,CONSO_TOTAL,NBR_SEAUX_MAX,CONSO_JOUR,GCP_CLIENT_CODE,StatusString)
                                    
                                    ##RECUPERATION DES BALLES
                                    msg("JOUR:"+str(CONSO_JOUR)+"/" +str(NBR_SEAUX_MAX)+" MAX","SOLDE : "+str(CREDIT_TOTAL-CONSO_TOTAL))
                                    LAST_MSG = "J:" + str(NBR_SEAUX_MAX-CONSO_JOUR) + " CR:"+str(CREDIT_TOTAL-CONSO_TOTAL)
                                    # msg("JOUR:"+str(NBR_SEAUX_MAX-CONSO_JOUR)+"/"+str(NBR_SEAUX_MAX)+"MAX","Patienter..")
                                    # time.sleep(2)
                                    # msg("SOLDE:"+str(CREDIT_TOTAL-CONSO_TOTAL)+"/"+str(CREDIT_TOTAL)+"MAX","Patienter...")
                                    time.sleep(2)
                                    #deconection de la carte
                                    # ---- MIFAREReader.MFRC522_StopCrypto1()
                                    
                                    t1 = threading.Thread(name='t1',target= declencherelay).start()
                                    msg("RECUPERER BALLES","MERCI")
                                    time.sleep(2)
                                    print("\n")
                                    continue_reading = True
                                    print("last message: ",bOkString)
                                except:
                                    bOkString="Carte retirée Avant ECRITURE"
                                    insert_passage(GCP_UID,TYPE_CARD, GCP_NOM,GCP_PRENOM,GCP_CLUB,DATE_CARD_VALID,DATE_LAST_PASS,CREDIT_TOTAL,CONSO_TOTAL,NBR_SEAUX_MAX,CONSO_JOUR,GCP_CLIENT_CODE,bOkString)
                                    print("Carte retirée Avant ECRITURE")
                                    continue_reading = False
                                    msg("CARTE RETIREE","TROP TOT")
                                    LAST_MSG = "CARTE ARRACHEE !"
                                    time.sleep(5)
                                
                               # time.sleep(0.5)      
                            else:
                                print("last message ms: ",bOkString)
                                insert_passage(GCP_UID,TYPE_CARD, GCP_NOM,GCP_PRENOM,GCP_CLUB,DATE_CARD_VALID,DATE_LAST_PASS,CREDIT_TOTAL,CONSO_TOTAL,NBR_SEAUX_MAX,CONSO_JOUR,GCP_CLIENT_CODE,bOkString)
                                print(bOkString,CONSO_JOUR)
                                msg("CREDIT RESTANT","       "+str(CREDIT_TOTAL-CONSO_TOTAL))
                                time.sleep(2)
                                msg("MAX SEAUX JOURS","ATTEINT "+str(CONSO_JOUR)+"/"+str(NBR_SEAUX_MAX))
                                LAST_MSG = "MAX JOUR (" + str(NBR_SEAUX_MAX) + ")"
                                time.sleep(2)
                                # msg("CREDIT RESTANT","       "+str(CREDIT_TOTAL-CONSO_TOTAL)+"/"+str(CREDIT_TOTAL))
                                # time.sleep(1)
                                
                        if continue_reading:
                            print("\n")
                            print("Uid: ",GCP_UID,"\n")
                            print("Type Card: ",TYPE_CARD,"\n")
                            print("NOM: ",GCP_NOM,"\n")
                            print("PRENOM: ",GCP_PRENOM,"\n")
                            print("CLUB: ",GCP_CLUB,"\n")
                            print("Date Limite De Validité: ",DATE_CARD_VALID,"\n")
                            print("Date Dernier Passage: ",DATE_LAST_PASS,"\n")
                            print("Date Du Jour: ",DATE_TODAY,"\n")
                            print("Crédit Cumulé: ",CREDIT_TOTAL,"\n")
                            print("Unités Consommées: ",CONSO_TOTAL,"\n")
                            print("CREDIT RESTANT: ",Solde,"\n")
                            print("MAX seaux: ",NBR_SEAUX_MAX,"\n")
                            print("Unités Consommées du jour: ",CONSO_JOUR,"\n")
                            print("Code CLIENT :",GCP_CLIENT_CODE,"\n")
                            print("BLOC3 12/13/14/15 :",GCP_CODE,"\n")
                            print("veuillez retirer votre Carte")
                            #msg("VEUILLEZ RETIRER","VOTRE CARTE")
                            #time.sleep(1)
                        else:
                            msg("CARTE RETIREE","TROP TOT")
                            LAST_MSG = "CARTE ARRACHEE !"
                            time.sleep(5)
                            
                        print("last Update: ",bOkString)
                    else:
                        print(bOkString,CREDIT_TOTAL,"/",CONSO_TOTAL)
                        print("last message: ",bOkString)
                        insert_passage(GCP_UID,TYPE_CARD, GCP_NOM,GCP_PRENOM,GCP_CLUB,DATE_CARD_VALID,DATE_LAST_PASS,CREDIT_TOTAL,CONSO_TOTAL,NBR_SEAUX_MAX,CONSO_JOUR,GCP_CLIENT_CODE,bOkString)
                else:
                    print(bOkString,"Date limite de validite",DATE_CARD_VALID)
                    insert_passage(GCP_UID,TYPE_CARD, GCP_NOM,GCP_PRENOM,GCP_CLUB,DATE_CARD_VALID,DATE_LAST_PASS,CREDIT_TOTAL,CONSO_TOTAL,NBR_SEAUX_MAX,CONSO_JOUR,GCP_CLIENT_CODE,bOkString)
                    # MIFAREReader.MFRC522_StopCrypto1()
                    print("last message: ",bOkString)
                    
                # -- MIFAREReader.MFRC522_StopCrypto1()
            else:
                print("Error Authentification ",B3S12,"- Bloc 3")
                msg("CARTE","INCONNUE")
                LAST_MSG = "CARTE INCONNUE !"
                time.sleep(1)
                # -- MIFAREReader.MFRC522_StopCrypto1()
        # si une carte a été insérée, boucler jusqu'à ce que la carte soit retirée
        if Card_Insert==1:
            Card_Insert = 0 # pour ne pas recommencer à la prochaine boucle sans carte
            msg(LAST_MSG,"RETIRER CARTE ...")
            i = 0
            MIFAREReader.MFRC522_StopCrypto1()
            boucle_attente = 1
            while boucle_attente:
                i=i+1
                (bOK,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
                # print("Attente retrait carte TAG 1 : ",i, " : ", bOK, " : ", TagType)
                if not bOK==MIFAREReader.MI_OK:
                    (bOK,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
                    print("Attente retrait carte : ",i, " : ", bOK, " : ", TagType)
                    if not bOK==MIFAREReader.MI_OK:
                        boucle_attente = False
                time.sleep(0.5)
            i = 0
        # Attendre une demie seconde avant de recommencer la boucle générale
        time.sleep(0.5)
        #
except KeyboardInterrupt:
    lcd_init()
    lcd_string("MACHINE ARRETEE",LCD_LINE_1)
    lcd_string("ESSAYEZ + TARD",LCD_LINE_2)
    


