import pandas as pd
import streamlit as st
import mysql.connector
import time
from st_aggrid import AgGrid
from streamlit_option_menu import option_menu
import pandas_bokeh
pandas_bokeh.output_notebook()
from bokeh.plotting import figure
from bokeh.palettes import Category20c
from bokeh.transform import cumsum
from bokeh.models import ColumnDataSource
import numpy as np
import mysql


st.set_page_config(page_title="Kiriman Ke Cabang dan Agen 2", layout='wide')


def init_connection():
    return mysql.connector.connect(**st.secrets["mysql"])


conn = init_connection()


def page_1():
    page_1= st.container()

def page_2():
    page_2= st.container()

def page_3():
    page_3= st.container()


selected2 = option_menu("Dashboard Operasional CitoXpress", ["Kiriman Belum Ada Status", "Kiriman Intracity Jakarta", "Volume Kiriman", "Analisis Historis"],
    icons=['bi bi-envelope-exclamation', 'bi bi-exclamation-circle', 'bi bi-boxes', 'gear'], 
    menu_icon="cast", default_index=0, orientation="horizontal")

if selected2=="Kiriman Belum Ada Status":
    page_1()
    
    query_1 = '''  
        select DATE_FORMAT(tanggal,'%M_%Y') as bln_thn, kdmani, d.kdpelanggan, d.nmpelanggan, sum(if(konid<>' ', 1, 0)) as 'no_status'  from tkonos a
        left join mpelanggan d on left(a.kdpelanggan,8) = d.kdpelanggan
        where tanggal>= concat(date_format((DATE_ADD(NOW(), INTERVAL -3 MONTH)),'%Y-%m'),-01)
        and tanggal<= now()
        and a.kdpelanggan not like 'CBH17002%' and a.pod='' and a.jenis not like 'I' 
        group by  kdmani, d.nmpelanggan, bln_thn
        order by tanggal asc
'''
    cursor = conn.cursor()
    cursor.execute(query_1)
    result1 = cursor.fetchall()

    @st.cache_data(ttl=600)
    def load_data(mysql1): 
        with conn.cursor() as cur:
            cur.execute(mysql1)
            return cur.fetchall()


    datafr=pd.DataFrame(result1)

    
    datafr.columns= ["bln_thn", "kdmani", "kd_pelanggan", "nm_pelanggan", "no_status"]
    datafr["no_status"] = datafr[["no_status"]].astype(int)

    datafr0=datafr.drop(["kdmani"], axis=1)
    datafr0= datafr.groupby(["bln_thn", "kd_pelanggan", "nm_pelanggan"], as_index=False)["no_status"].sum()
    
    datafr1= pd.DataFrame(datafr0)
    datafr1=datafr1.sort_values(by=["no_status"], ascending=False)
   
    datacab=datafr.drop(["kd_pelanggan", "nm_pelanggan"], axis=1)

    

    

    col1, col2 = st.columns(2, gap= "medium")

    with col1:

        bulan=datafr['bln_thn'].drop_duplicates().sort_index(ascending=True)
        pilihan=st.radio(" ", key="visibility", options= bulan, label_visibility= "collapsed",horizontal=True)
    
        hasil = datafr1[datafr1["bln_thn"] == pilihan]
        total=int(hasil["no_status"].sum())
        bold = (f"**{total}**")
  

        localtime = time.asctime( time.localtime(time.time()) )
        hari_ini=(time.strftime("%d-%m-%Y  %H:%M:%S", time.localtime()))
        
        
        AgGrid(hasil)

        st.markdown( f" :green[{hari_ini}] ")

     

    with col2:

        col2a, col2b, col2c = st.columns((1,3,1), gap="small")

        with col2b:
            fontsize = 35
            x=total
            test= f"""<p style=' color: #3288bd; text-align: center;
                        font-size: {fontsize}px; 
                        border-radius: 8px; 
                        border: 5px solid #3288bd;
                        padding-left: 0px; 
                        padding-top: 25px; 
                        padding-bottom: 25px;
                        line-height:3px;'>
                        {x} Kiriman
                        """

            st.markdown(test, unsafe_allow_html=True)
        
        
        hasil2 = datacab[datacab["bln_thn"] == pilihan] 
        hasil2a = hasil2.groupby(["kdmani"])["no_status"].sum().reset_index(name='tanpa_status').sort_values(["tanpa_status"], ascending=False).head(10)



        list_wrn=["#B8860B","#DAA520","#FFD700","#F0E68C","#90EE90",
        "#8FBC8F","#66CDAA","#008080",
        "#48D1CC","#B0E0E6","#00BFFF",
        "#9370DB","#D8BFD8","#DA70D6",
        "#FF69B4","#FFB6C1","#F5DEB3",
        "#CD853F","#DEB887","#BC8F8F",
        "#FFDAB9","#B0C4DE","#E6E6FA"]


        wrn_sama=["#3288bd","#3288bd","#3288bd ","#3288bd ","#3288bd ","#3288bd ",
        "#3288bd","#3288bd","#3288bd","#3288bd ","#3288bd","#3288bd ","#3288bd ","#3288bd ",
        "#3288bd ","#3288bd ","#3288bd","#3288bd","#3288bd","#3288bd ","#3288bd ","#3288bd ",
        "#00BFFF","#00BFFF","#00BFFF","#00BFFF","#00BFFF","#00BFFF","#00BFFF","#00BFFF"]
       
        list_np=np.array(list_wrn)
        list_sama=np.array(wrn_sama)
        

        listnostatus=list(hasil2a['tanpa_status'])
        listkdmani=list(hasil2a['kdmani'])

            
        x_line = listkdmani
        counts1 = listnostatus
        fr_len=len(listkdmani)
        color_ts=list_np[0:fr_len]

        color_sama=list_sama[0:fr_len]
        
        y_up=np.max(listnostatus)
    
        source_2 = ColumnDataSource(data=dict(x_line=x_line, counts1=counts1, color=color_sama))

        TOOLTIPS = [
        ("", "@x_line - @counts1"),
        ]

        px1 = figure(x_range=x_line, y_range=(0, y_up+4), height=500, tooltips=TOOLTIPS,
        toolbar_location=None,tools="")
        px1.vbar(x="x_line", top="counts1", width=0.7, color="color", legend_field="x_line", source=source_2)
    
        px1.xgrid.grid_line_color = None
        px1.plot_width=500
        px1.legend.orientation = "horizontal"
        px1.legend.location = "top_center"
        px1.add_layout(px1.legend[0], 'below')

        st.bokeh_chart(px1,use_container_width=True)
   
            

if selected2=="Kiriman Intracity Jakarta":
    page_2()

    query_2="""
    select konid, tanggal, asal, kdmani, jenis, c.nmpelanggan, penerima, kdproduk, berat, b.nmkota from tkonos a
    left join mkota b on b.kdkota=a.tujuan
    left join mpelanggan c on c.kdpelanggan = left(a.kdpelanggan,8)
    where Datediff(CURRENT_DATE,tanggal)>=14 and 
    kdmani in('CBH', 'MDE', 'MDT', 'MDA', 'MDJ') and pod= " "
    and a.kdpelanggan not like 'CBH17002%' and jenis not like 'I' and tanggal>='2022-12-01'
    order by tanggal asc
    
    """

    cursor = conn.cursor()
    cursor.execute(query_2)
    result2 = cursor.fetchall()

    @st.cache_data(ttl=600)
    def load_data2(mysql2): 
        with conn.cursor() as cur:
            cur.execute(mysql2)
            return cur.fetchall()
    

    datafr2=pd.DataFrame(result2)

    
    
    datafr2.columns= ["konid" ,"tanggal", "ktr_asal", "ktr_tujuan", "jenis", "pengirim", "penerima", "kdproduk", "berat", "nm_kota" ]
    datafr2["tanggal"]=time.strftime("%d-%m-%Y ")
    

    hasil3=datafr2[["konid","tanggal", "ktr_asal", "ktr_tujuan", "pengirim", "penerima", "kdproduk", "berat", "nm_kota" ]]
    total_hasil3=hasil3[["konid"]].count()
  
    
    groupby_hasil3= hasil3.groupby(["ktr_tujuan"])["konid"].count().reset_index(name='count').sort_values(['count'], ascending=False) 
    groupby_hasil4= hasil3.groupby(["pengirim"])["konid"].count().reset_index(name='count').sort_values(['count'], ascending=False) 

    col3, col4 = st.columns(2 , gap= "medium")

    with col3:

        from math import pi
        from bokeh.palettes import Category20c
        from bokeh.plotting import figure
        from bokeh.transform import cumsum
        from bokeh.models import Legend
    


        groupby_hasil4['angle'] = groupby_hasil4['count']/groupby_hasil4['count'].sum() * 2*pi
        groupby_hasil4['color'] = Category20c[len(groupby_hasil4["pengirim"])]

        z=100*(groupby_hasil4['count']/groupby_hasil4['count'].sum())
        groupby_hasil4['count1']=z

        sep = []
        for i in range(len(groupby_hasil4.index)):
            sep.append(':  ')


        groupby_hasil4[["awal", "tengah", "belakang", "akhir"]]=groupby_hasil4["pengirim"].str.split(" ", n = 3, expand = True)
        groupby_hasil4["update"]=groupby_hasil4["awal"].str.cat(groupby_hasil4["tengah"], sep = " ")
        
        groupby_hasil4['legend'] = groupby_hasil4['update'] + sep + groupby_hasil4['count'].astype(str)


        p = figure(plot_height=350, title="Data Kiriman Belum Ada Status Berdasarkan Pelanggan ", toolbar_location="above",
           tools="hover", tooltips="@pengirim: @count1{0.2f} %", x_range=(-.5, .5))

        p.annular_wedge(x=0, y=1,  inner_radius=0.18, outer_radius=0.35, direction="anticlock", 
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        line_color="white", fill_color='color', legend="legend", source=groupby_hasil4)

       
        
        
        

       

        p.axis.axis_label=None
        p.axis.visible=False
        p.grid.grid_line_color = None
        p.legend.location = "center"
        p.add_layout(p.legend[0], 'right')

        st.bokeh_chart(p)

        
        

        
        localtime = time.asctime( time.localtime(time.time()) )
        hari_ini=(time.strftime("%d-%m-%Y  %H:%M:%S", time.localtime()))
        tgl_ini=(time.strftime("%d-%m-%Y ", time.localtime()))

        st.caption(f""" 
        1. Data yang digunakan adalah Kiriman Intracity Jakarta periode:  01-12-2022  s.d.  {tgl_ini} 
        2. Data Kiriman tersebut di atas adalah Kiriman yang belum ada status selama 14 hari ke atas dari tanggal Conote
    
    """)
        
        
        st.markdown( f" :green[{hari_ini}] ")

        
    

    with col4:
        p1=groupby_hasil3.plot_bokeh(
        kind='bar',
        x='ktr_tujuan',
        y='count',
        xlabel='Kurir dan Mitra Jakarta',
        ylabel='Kiriman No Status',
        title='Data Kiriman Belum Ada Status Berdasarkan Kurir Intracity / Mitra',
        color="#3288bd"
  
        )
        st.bokeh_chart(p1)
    
if selected2=="Volume Kiriman":
    page_3()

    query_3="""
    select year(tanggal) as tahun, MONTHNAME(tanggal) as bulan,  DATE_FORMAT(tanggal,'%M_%Y') as bln_thn,
    COUNT(konid) as qty_pcs, round(sum(berat),0) as berat_kg from 
    tkonos where tanggal >='2023-01-01' and tanggal<=NOW() and kdpelanggan not like 'CBH17002%' 
    group by month(tanggal), year(tanggal)
    order by year(tanggal), month(tanggal) asc
    """

    cursor = conn.cursor()
    cursor.execute(query_3)
    result3 = cursor.fetchall()

    @st.cache_data(ttl=600)
    def load_data3(mysql3): 
       with conn.cursor() as cur:
            cur.execute(mysql3)
            return cur.fetchall()
    

    datapage3=pd.DataFrame(result3)
    st.text(datapage3.info)

    datapage3.columns= ["tahun","bulan" ,"bln_thn", "qty_pcs", "berat_kg"]
    datapage3["qty_pcs"] = datapage3[["qty_pcs"]].astype(int)
    datapage3["berat_kg"] = datapage3[["berat_kg"]].astype(int)

    p4=datapage3.plot_bokeh(
        kind='bar',
        x='bln_thn',
        y='berat_kg',
        xlabel='Bulan Tahun',
        ylabel='Kiriman No Status',
        title='Data Kiriman',
        color="#3288bd")
  
    st.bokeh_chart(p4)
