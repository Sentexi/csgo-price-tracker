import numpy as np
import os
import argparse
from bs4 import BeautifulSoup
import requests
import re
import csv
from tqdm import tqdm
import time
import json
import pickle
import random
import statistics
import urllib.request

def load_collection(Textfile):
    collection = []
    with open(Textfile, 'r') as file:
        reader = file.readlines()
        for row in reader:
            collection.append(row)
    return collection

#loads the html template with javascripts, Bootstrap and some other stuff    
def load_template(Textfile):
    Template = []
    with open(Textfile, 'r') as file:
        reader = file.readlines()
        for row in reader:
            Template.append(row)
    return Template
    
#Reads in the first 57 lines containing head and navbar    
def create_html_foundation():
    Document = []
    End = []
    Template = load_template("TemplateTradeUp.html")
    for i in range(258):
        if i <= 28:
            Document.append(Template[i])
        if i > 251:
            End.append(Template[i])
    #Decouple Navbar from rest to make it easier to scale
    Navbar = load_template("Navbar.html")
    for line in Navbar:
        Document.append(line)
    return Document , End
    
#Writes everything to a html
def write(Document, name):
    with open("{}.html".format(name), 'w') as file:
        for line in Document:
            file.write(line) 

#Checks if image is in cache, else Extracts Image from a given url     
def ExtractImage(url,nicename):
    #Check if Cache directory exists, else create one
    if os.path.isdir(cache) == False:
        os.mkdir(cache)
    nicename = nicename.replace("|" , " ")
    nicename = "{}.png".format(nicename)
    imgpath = r"{}".format(os.path.join(cache,nicename))
    #Check wether image exists, else scrape it
    if os.path.isfile(imgpath) == False:
        #get img url from steam url
        request = requests.get(url)
        soup = BeautifulSoup(request.text, 'html.parser')
        img = soup.find_all('img')
        try:
            img = img[7].get("src")
            urllib.request.urlretrieve(img, imgpath)
            if os.stat(imgpath).st_size < 5000:
                print("caching failed")
                os.remove(imgpath)
                imgpath =  r"{}".format(os.path.join(cache,"Dummy.png"))
        except:
            print("to many attempts at scraping, waiting 180s")
            time.sleep(180)
            request = requests.get(url)
            soup = BeautifulSoup(request.text, 'html.parser')
            img = soup.find_all('img')
            try:
                img = img[7].get("src")
                urllib.request.urlretrieve(img, imgpath)
                if os.stat(imgpath).st_size < 5000:
                    print("caching failed")
                    os.remove(imgpath)
                    imgpath = imgpath = r"{}".format(os.path.join(cache,"Dummy.png"))
            except:
                print("Second attempt failed, using dummy")            
                imgpath = imgpath = r"{}".format(os.path.join(cache,"Dummy.png"))            
    return imgpath
    

        

#Creates readable item name from url
def CreateNiceName(url):
    #Split URL by slashes
    split = url.split('/')
    #The last one is the name
    rawname = split[-1]
    #Remove weird delimiter signs
    nicename = rawname.replace("%20", " ")
    nicename = nicename.replace("%28", "(")
    nicename = nicename.replace("%29", ")")
    nicename = nicename.replace("%7C","|")
    return nicename    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Creates a bootstrapped collection based on an input tsv')
    parser.add_argument('--collection', type=str,  help='Textfile from which assets are accumulated',required=True)
    
    args = parser.parse_args()
    collection = args.collection

    #Init path, cwd can be anything. Is the location of image cache
    cache = os.path.join(".","collection_cache")

    #Create html and Navbar, load End
    Document, End = create_html_foundation()
    
    #TODO Read in collection, separate by tab
    collection_text = load_collection(collection)
    
    #Begin Div
    Document.append("    <div class=\"p-3 mb-1 bg-gradient-dark text-white\" style=\"background-color:black\">\n")
    Document.append("		<div class=\"row\" row-no-margin>\n")
    Document.append("        <div class=\"col-12 col-xs-12 col-sm-12 col-lg-12 col-no-padding\">\n")
    Document.append("		<div class=\"row\">\n")
    
    for i in tqdm(range(len(collection_text))):
        col = collection_text[i].split('\t')
        nicename = CreateNiceName(col[0])
        imgpath = ExtractImage(col[0],nicename)
        #CreateDiv()
        Document.append("		  <div class=\"pr-3 col-6 col-xs-6 col-sm-4 col-lg-2 col-no-padding\">\n")
        Document.append("              <figure> \n")
        Document.append("			    <a href=\"{}\"> \n".format(col[0]))
        Document.append("			    <img width=100% class=\"img-responsive\" src=\"{}\">\n".format(imgpath))
        Document.append("			    </a>\n")
        Document.append("                <figcaption>{}x {}</figcaption>  \n".format(col[1],nicename))
        Document.append("              </figure> \n")
        Document.append("            </div> \n")

    #End Div
    Document.append("			    </div></div></div></div>\n")
    
    #Cache images and create nice name
    
    
    #Close body and html
    for line in End:
        Document.append(line)

    #Grab name from collection name, truncating the ending
    name = collection.split('.')
    name = "{}Composition".format(name[0])
    #At the end, write to file
    write(Document, name)        