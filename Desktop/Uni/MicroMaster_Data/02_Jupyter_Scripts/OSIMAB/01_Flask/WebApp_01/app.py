from flask import Flask, render_template, request
import pandas as pd
import numpy as np
from flask import Flask, render_template_string
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SelectField
from wtforms.validators  import DataRequired 
import uuid, utm, folium
from scipy.spatial.distance import cdist

app = Flask(__name__)
app.secret_key = 'secret'

dfZN = pd.read_csv('Br_ZN.csv',sep=';',decimal =',',thousands='.',index_col=0,encoding='latin-1')
dfZS = pd.read_csv('Jawe2016.csv',sep=';',decimal =',',thousands='.',index_col=False,encoding='latin-1')

# Berechnung DistanzMatrix
arrKoBr=dfZN[['x [m] UTM32','y [m] UTM32']].values
arrKoZS=dfZS[['Koor_UTM32_E','Koor_UTM32_N']].values
Y = cdist(arrKoBr,arrKoZS, 'euclidean')

dfDistanz=pd.DataFrame(data=Y,index=dfZN['bwnr'].values,columns=dfZS['DZ_Nr'].values)

name_list=[(idx, row) for idx, row in dfZN['bwnr'].iteritems()]
dis_list=[(dD*1000, '< '+str(dD)+' km') for dD in np.arange(10,110,10)]

class inputForm(FlaskForm):
    selFieldBW = SelectField(u"BW-NR", [], choices=name_list)
    selFieldType = SelectField(u"Zählstellen", [], choices=[(0,'Alle'),(1,'Auf gleicher Straße')])
    selFieldD = SelectField(u"Im Umkreis", [], choices=dis_list)

def createMap(idxBr,flagOnSt,thD):
  # Auswahl Brücke
  serSel=dfZN.iloc[idxBr]
  serDZS=dfDistanz.iloc[idxBr]

  intDZnr=serDZS.index[serDZS<thD]

  if flagOnSt:
      intDZOnSt=dfZS.loc[(dfZS['Str_Kl'] == serSel['Str_Kl']) & (dfZS['Str_Nr'] == serSel['Str_Nr'])]['DZ_Nr'].values
      intDZnr=np.intersect1d(intDZnr,intDZOnSt)
      

  koUTM=serSel[['x [m] UTM32','y [m] UTM32']].values
  koWSG=utm.to_latlon(koUTM[0],koUTM[1],zone_number=32,zone_letter='U')

  map_1 = folium.Map(location=[51.5, 10],
                     zoom_start=5.5)

  # Marker Brücke
  iframe = folium.IFrame(html=serSel.to_frame().to_html(), width=500, height=300)
  popup = folium.Popup(iframe, max_width=2650)

  folium.Marker(koWSG,
                popup=popup,
                icon=folium.Icon(color='red')
               ).add_to(map_1)

  for nr in intDZnr:
      dfZS_Data=dfZS.loc[dfZS['DZ_Nr'] ==nr] # Daten
      
      koUTM1=dfZS_Data[['Koor_UTM32_E','Koor_UTM32_N']].values.squeeze() # Koordinaten
      koWSG1=utm.to_latlon(koUTM1[0],koUTM1[1],zone_number=32,zone_letter='U')

      # Marker Zählstelle
      iframe1 = folium.IFrame(html=dfZS_Data.T.to_html(), width=500, height=300)
      popup1 = folium.Popup(iframe1, max_width=2650)

      folium.Marker(koWSG1,
                popup=popup1,
                icon=folium.Icon(color='blue')
               ).add_to(map_1)

  fileNameMap='Map_Temp.html'
  map_1.save('templates/Map_Temp.html')
  return fileNameMap # Return eigentlich nicht sonderlich sinnvoll, aber egal


@app.route('/', methods=('GET', 'POST'))
def main():

    form = inputForm()
    fileNameMap='Karte_BWNr_6733656.html'

    if request.method == 'POST':
      idxBr=int(form.selFieldBW.data)
      flagOnSt=int(form.selFieldType.data)
      thD=int(form.selFieldD.data)

      fileNameMap=createMap(idxBr,flagOnSt,thD)
      return render_template("index.html",fileNameMap=fileNameMap,form=form)
	
    return render_template("index.html",fileNameMap=fileNameMap,form=form)

if __name__ == "__main__":
    app.debug = True 
    app.run()
