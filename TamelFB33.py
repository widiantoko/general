import pandas as pd
import pandas_bokeh
pandas_bokeh.output_notebook()
import streamlit as st
import mysql.connector
import time
from streamlit_option_menu import option_menu
from bokeh.plotting import figure
from bokeh.transform import cumsum
from bokeh.models import ColumnDataSource, Range1d, LabelSet
import numpy as np
import mysql
from bokeh.plotting import figure
import math
from datetime import datetime, timedelta, timezone






st.set_page_config(page_title="Kiriman Ke Cabang dan Agen", layout='wide')


@st.cache_data(ttl=600)
def fetch_from_db(query, db_key):
    """Fetch data from MySQL database with automatic caching"""
    conn = mysql.connector.connect(**st.secrets[db_key], use_pure=True)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(query)
    result = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return pd.DataFrame(result)




def page_1():
    return st.container()

def page_2():
    return st.container()

def page_3():
    return st.container()

def page_4():
    return st.container()


selected2 = option_menu("Dashboard Operasional CitoXpress", ["Kiriman Belum Ada Status", "Kiriman Intracity Jakarta", "Volume Kiriman", "Review Kinerja"],
    icons=['bi bi-envelope-exclamation', 'bi bi-exclamation-circle', 'bi bi-boxes', 'gear'], 
    menu_icon="cast", default_index=0, orientation="horizontal")

if selected2=="Kiriman Belum Ada Status":
    page_1()
    
    query_1 = '''  
        select konid, DATE_FORMAT(tanggal,'%M_%Y') as bln_thn, kdmani, 
6 * (DATEDIFF(CURRENT_DATE, tanggal) DIV 7) + MID('0123455501234445012333450122234501112345000123450', 7 * WEEKDAY(tanggal) + WEEKDAY(CURRENT_DATE) + 1, 1) as 'diff2',
d.kdpelanggan, d.nmpelanggan, kdproduk, kdkirim  from tkonos a
        left join mpelanggan d on left(a.kdpelanggan,8) = d.kdpelanggan
        where tanggal>= concat(date_format((DATE_ADD(NOW(), INTERVAL -3 MONTH)),'%Y-%m'),-01)
        and tanggal<= now()
        and a.kdpelanggan not like 'CBH17002%' and a.pod=' ' and a.jenis not like 'I' and a.kdproduk in ('N', 'U', 'T', 'D', 'C', 'P')
        and a.awbno <> " "
        order by tanggal asc

    '''
    
    datafr = fetch_from_db(query_1, "mysql01")
    datafr.columns = ["konid", "bln_thn", "kdmani", "diff2", "kd_pelanggan", "nm_pelanggan", "kdproduk", "kdkirim"]
    datafr['nm_pelanggan'] = datafr['nm_pelanggan'].str.replace(",",' ')    
    datafr[["awal", "tengah", "belakang", "akhir"]]=datafr["nm_pelanggan"].str.split(" ", n = 3, expand = True)
    datafr["pelanggan"]=datafr["awal"] + " " + datafr["tengah"] 
    datafr["diff2"] = datafr[["diff2"]].astype(int)





    for i, row in datafr.iterrows():
        hasil1 = ''
        if (row['diff2'] >= 0 and row['diff2'] <4):
            hasil1 = 'a. 0 - 3 hari'
        elif (row['diff2'] > 3 and row['diff2'] <8):
            hasil1 = 'b. 4 - 7 hari'
        elif (row['diff2'] >7  and row['diff2'] <15):
            hasil1 = 'c. 8 - 14 hari'
        elif (row['diff2'] > 14 and row['diff2'] <31):
            hasil1 = 'd. 15 - 30 hari'
        elif (row['diff2'] > 30  and row['diff2'] <61):
            hasil1 = 'e. 31 - 60 hari'
        else:
            hasil1 = 'f. 61 hari - dst'
    
        datafr.at[i, 'cluster_LT'] = hasil1


    

    col1, col2 = st.columns(2, gap= "medium")

    with col1:

        bulan=datafr['bln_thn'].drop_duplicates().sort_index(ascending=True)
        pilihan=st.radio(" ", key="visibility", options= bulan, label_visibility= "collapsed",horizontal=True)
    

        
        data_hasil= datafr.groupby(['bln_thn']).apply(lambda x: x[x['bln_thn'] == pilihan]['konid'].count())
        data_kdkirim= datafr.groupby(["kdkirim"]).apply(lambda x: x[x['bln_thn'] == pilihan]['konid'].count()).reset_index(name='jumlah')
        data_plgn= datafr.groupby(["nm_pelanggan", "kdproduk"])["konid"].count().reset_index(name='no_status').sort_values(["no_status"], ascending=False).head(12)
        
        total=sum(data_hasil)
        bold = (f"**{total}**")

        #pkt=list(data_kdkirim)[0]
        #doc=list(data_kdkirim)[1]
        pkt=data_kdkirim.loc[data_kdkirim.kdkirim == 'C', 'jumlah'].iloc[0]
        doc=data_kdkirim.loc[data_kdkirim.kdkirim == 'D', 'jumlah'].iloc[0]


        hasil2 = datafr[datafr["bln_thn"] == pilihan] 
        hasil2a = hasil2.groupby(["kdmani"])["konid"].count().reset_index(name='no_status').sort_values(["no_status"], ascending=False).head(12)
        hasil2b = hasil2.groupby(["kdmani" ,"bln_thn" ,"cluster_LT"])["konid"].count().reset_index(name='no_status').sort_values(["no_status"], ascending=False)
        hasil2c = hasil2.groupby(["pelanggan" ,"bln_thn" ,"kdproduk"])["konid"].count().reset_index(name='rekap').sort_values(["rekap"], ascending=False)

       

        pivot_2c=hasil2c.pivot_table(values='rekap', index = ['pelanggan'], 
                     columns= ['kdproduk'], aggfunc= 'sum',  margins = True, margins_name='sum').fillna(0)
        
        pivot_2c.rename(columns={'N': 'Normal', 'U': 'Urgent', 'T': 'Top Urgent', 'D': 'Darat',
        'C': 'Trucking' , 'P': 'Premium' }, inplace=True)
      
                
        pivot_2c.reset_index(inplace=True)
        #pivot_2c["sum"]=pivot_2c.sum(axis=1)
        update_2c = pivot_2c.drop(pivot_2c.index[int(len(pivot_2c))-1])

        
        final=update_2c.sort_values(by=["sum"], ascending=False).head(12)



        def round_up(n, decimals=0):
            multiplier = 10 ** decimals
            return math.ceil(n * multiplier) / multiplier


        xy=int(len(final.columns.values))
        final2=list(final.columns.values)[1 : xy-1]
        upper_lmt=round_up(final["sum"].nlargest(1)*1.1, -1)


        
        chart=ColumnDataSource(final)
        pelanggan=final["pelanggan"]
        
        
        wr = {'Normal': '#64B5F6',
        'Urgent':'#1565C0',
        'Top Urgent':'#FF8A80',
        'Trucking':'#1DE9B6',
        'Darat':'#FDD835',
        'Premium': '#F48FB1'}

        warni=[wr[x] for x in final2]
        ok=list(warni) 

        

       

        ps = figure(x_range=pelanggan, height=480,
           toolbar_location=None, tools="hover", tooltips="$name : @$name")

        ps.vbar_stack(final2, x='pelanggan', width=0.8, source=chart, color=ok,
             legend_label=final2)



        ph = figure(y_range=pelanggan, height=520, tools="hover" , tooltips="$name : @$name",
           toolbar_location=None)

        ph.hbar_stack(final2, y='pelanggan', height=0.7, color=ok, source=chart,
             legend_label= final2)

        

        ph.ygrid.grid_line_color = None
        ph.x_range=Range1d(0, upper_lmt)
        ph.legend.location = "top_left"
        ph.legend.orientation = "horizontal"
        ph.axis.minor_tick_line_color = None
        ph.add_layout(ph.legend[0], 'below')
        ph.outline_line_color = None # type: ignore



       
        #ps.y_range = Range1d(0, upper_lmt)
        #ps.xgrid.grid_line_color = None
        #ps.axis.minor_tick_line_color = None
        #ps.legend.location = "center"
        #ps.legend.orientation = "horizontal"
        #ps.add_layout(ps.legend[0], 'below')
        #ps.outline_line_color = None  # type: ignore
        #   pv.add_layout(lblpv)
        #   pv.add_layout(Labels)
  
      
        #st.bokeh_chart(ps)

        st.bokeh_chart(ph)
      
    
    
        tz_offset = timezone(timedelta(hours=7))  # UTC+7 for Asia/Jakarta
        hari_ini = datetime.now(tz_offset).strftime("%d-%m-%Y | %H:%M:%S")
        st.markdown( f" :green[{hari_ini}] ")

        
     

    with col2:




        col2a,  col2c = st.columns((2,3), gap="small")

        with col2a:
            fontsize = 30
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

            



        with col2c:
            fontsize = 30
            link='<"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.0/css/all.css"">'
            test= f"""<p style=' color: #3288bd; text-align: center;
                        font-size: {fontsize}px; 
                        border-radius: 8px; 
                        border: 5px solid #3288bd;
                        padding-left: 0px; 
                        padding-top: 25px; 
                        padding-bottom: 25px;
                        line-height:3px;'>
                        <i class="far fa-facebook"></i>
                        {doc} Dok + {pkt} Paket 
                        """

            st.markdown(test, unsafe_allow_html=True)


        

        listkdmani=list(hasil2a["kdmani"])
        
        pivot_LT=hasil2b[hasil2b.kdmani.isin((listkdmani))].pivot_table(values='no_status',index=['kdmani'], columns=['cluster_LT'], aggfunc=np.sum).fillna(0)
 
        

        join_inner = pd.merge(hasil2a, pivot_LT, how="left", on=['kdmani'])
        join_inner_drop=join_inner.drop(["no_status"], axis=1)
        r_join=len(join_inner_drop.columns.values)

        bln_cluster_drop=list(join_inner_drop.columns.values)[1:r_join]

        clt = ['a. 0 - 3 hari',
        'b. 4 - 7 hari', 'c. 8 - 14 hari','d. 15 - 30 hari',
        'e. 31 - 60 hari','f. 61 hari - dst']

        b=len(join_inner.columns.values)  
        b1=list(join_inner.columns)[0:b]      
        
        kdmani_join_in=list(join_inner["kdmani"])      
        bln_cluster=[i for i in clt if i in b1]
       
       
        kdmani = kdmani_join_in
        years = bln_cluster
  
        warna2 = {'a. 0 - 3 hari': '#9CCC65',
        'b. 4 - 7 hari':'#E6EE9C',
        'c. 8 - 14 hari':'#FFF59D',
        'd. 15 - 30 hari':'#FFD54F',
        'e. 31 - 60 hari': '#FFB74D',
        'f. 61 hari - dst': '#FF5722'}

        warna_sesuai=[warna2[x] for x in bln_cluster]
        oke=list(warna_sesuai) 

      
        lbr_vbar=500/len(kdmani_join_in)
        list_vbar = list(range(1, len(kdmani_join_in)+1))
        join_inner["x_posisi"]= [int(i) for i in[i*lbr_vbar - 0.5*lbr_vbar + i*5 for i in list_vbar]]
        

       

        def round_up(n, decimals=0):
            multiplier = 10 ** decimals
            return math.ceil(n * multiplier) / multiplier

        vol_cab=join_inner["no_status"].nlargest(1)
  

        y_atas=round_up(1.15*vol_cab, -1)

        join_inner["y_posisi"]  = [int(i) for i in join_inner['no_status']*400/y_atas + 5]

        join_inner['label']=['{:.0f}'.format(val) for val in join_inner['no_status']]

      

        data_chart=ColumnDataSource(join_inner)

        pv = figure(x_range=kdmani, height=480,
           toolbar_location=None, tools="hover", tooltips="$name @kdmani: @$name")

        pv.vbar_stack(years, x='kdmani', width=0.8, color=oke, source=data_chart,
             legend_label=years)


        Labels = LabelSet(x='x_posisi', y='y_posisi', text='label' ,text_color="grey", x_offset=0, y_offset=0,
                 text_baseline="middle", text_font_size='10pt', text_font_style= 'italic', source=data_chart, text_align='center',
                 x_units='screen', y_units='screen',  
                 render_mode='canvas')   
        
        #lblpv=Label(x=22, y=360, text="test", x_units="screen", y_units="screen")

        pv.y_range = Range1d(0, y_atas)
        pv.xgrid.grid_line_color = None
        pv.axis.minor_tick_line_color = None
        pv.legend.location = "center"
        pv.legend.orientation = "horizontal"
        pv.add_layout(pv.legend[0], 'below')
        pv.outline_line_color = None  # type: ignore
        #pv.add_layout(lblpv)
        #pv.add_layout(Labels)
  
    

        st.bokeh_chart(pv)
             
if selected2=="Kiriman Intracity Jakarta":
    page_2()

    query_2="""
    select konid, tanggal, asal, kdmani, jenis, c.nmpelanggan, penerima, kdproduk, berat, b.nmkota from tkonos a
    left join mkota b on b.kdkota=a.tujuan
    left join mpelanggan c on c.kdpelanggan = left(a.kdpelanggan,8)
    where Datediff(CURRENT_DATE,tanggal)>=14 and 
    kdmani in('CBH', 'MDE', 'MDT', 'MDA', 'MDJ') and pod= " "
    and a.kdpelanggan not like 'CBH17002%' and jenis not like 'I' and tanggal>='2025-01-01'
    order by tanggal asc
    
    """

    datafr2 = fetch_from_db(query_2, "mysql01")
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
    
        color_don = [
'#48D1CC','#9370DB','#008080','#8FBC8F','#DA70D6',
'#0000FF','#FFB6C1','#F5DEB3','#BC8F8F','#FFDAB9',
'#E6E6FA','#B0C4DE','#D8BFD8','#EEE8AA','#B0E0E6',
'#DB7093','#90EE90','#66CDAA','#FF69B4','#DEB887',
'#FFD700','#CD853F','#DAA520','#F0E68C','#87CEEB',
'#483D8B','#7FFF00','#228B22','#8B4513','#708090']


        color2= ['#ef9a9a','#f48fb1','#ce93d8','#b39ddb',
'#9fa8da','#90caf9','#81d4fa','#80deea','#80cbc4',
'#a5d6a7','#c5e1a5','#e6ee9c','#fff59d','#ffe082',
'#ffcc80','#ffab91','#bcaaa4','#e57373','#f06292',
'#ba68c8','#9575cd','#7986cb','#64b5f6','#4fc3f7',
'#4dd0e1','#4db6ac','#81c784','#aed581','#dce775',
'#fff176','#ffd54f','#ffb74d','#ff8a65','#a1887f',
'#ef5350','#ec407a','#ab47bc','#7e57c2','#5c6bc0',
'#42a5f5','#29b6f6','#26c6da','#26a69a','#66bb6a',
'#9ccc65','#d4e157','#ffee58','#ffca28','#ffa726','#ff7043','#8d6e63']


        groupby_hasil4['angle'] = groupby_hasil4['count']/groupby_hasil4['count'].sum() * 2*pi
        groupby_hasil4['color'] = color2[0:len(groupby_hasil4["pengirim"])]
        #groupby_hasil4['color'] = Category20c[len(groupby_hasil4["pengirim"])]
    


        z=100*(groupby_hasil4['count']/groupby_hasil4['count'].sum())
        groupby_hasil4['count1']=z

        sep = []
        for i in range(len(groupby_hasil4.index)):
            sep.append(':  ')


        groupby_hasil4[["awal", "tengah", "belakang", "akhir"]]=groupby_hasil4["pengirim"].str.split(" ", n = 3, expand = True)
        groupby_hasil4["update"]=groupby_hasil4["awal"].str.cat(groupby_hasil4["tengah"], sep = " ")
        
        #groupby_hasil4['legend'] = groupby_hasil4['update'] + sep + groupby_hasil4['count'].astype(str)
        groupby_hasil4['legend'] = groupby_hasil4['update'] + " : " + groupby_hasil4['count'].astype(str)


        p = figure(plot_height=600, title="Data Kiriman Belum Ada Status Berdasarkan Pelanggan ", toolbar_location="above",
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
        #hari_ini=(time.strftime("%d-%m-%Y  %H:%M:%S", time.localtime()))
        tgl_ini=(time.strftime("%d-%m-%Y ", time.localtime()))


        tz_offset = timezone(timedelta(hours=7))  # UTC+7 for Asia/Jakarta
        hari_ini = datetime.now(tz_offset).strftime("%d-%m-%Y | %H:%M:%S")

        st.caption(f""" 
        1. Data yang digunakan adalah Kiriman Intracity Jakarta periode:  01-01-2025  s.d.  {tgl_ini} 
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
    select year(tanggal) as tahun, MONTHNAME(tanggal) as bulan,  DATE_FORMAT(tanggal,'%b_%y') as bln_thn,
    COUNT(konid) as qty_pcs, round(sum(berat),0) as berat_kg from 
    tkonos where tanggal >='2025-10-01' and tanggal<=NOW() and kdpelanggan not like 'CBH17002%' and (kdpelanggan like 'CBH%' 
    or kdpelanggan like 'CTG%' 
    or kdpelanggan like 'CBO%' 
    or kdpelanggan like 'CBK%') 
    and kdproduk in ('N', 'U', 'T', 'D', 'P')
    group by month(tanggal), year(tanggal)
    order by year(tanggal), month(tanggal) asc
    """

    datapage3 = fetch_from_db(query_3, "mysql01")
    datapage3.columns= ["tahun","bulan" ,"bln_thn", "qty_pcs", "berat_kg"]
    datapage3["qty_pcs"] = datapage3[["qty_pcs"]].astype(int)
    datapage3["berat_kg"] = datapage3[["berat_kg"]].astype(int)

    df2024 = pd.read_csv('data/vol2024_2025_streamlit.csv', sep=',')
    df_combined = pd.concat([df2024, datapage3], ignore_index=True)
    
    #st.dataframe(datapage3)

    data2024=df_combined[df_combined["tahun"]==2024]
    data2025=df_combined[df_combined["tahun"]==2025]
    data2026=df_combined[df_combined["tahun"]==2026]

    bulanku = df_combined['bulan'].unique().tolist()
    tahunku = df_combined['tahun'].unique().tolist()

    #bln_thn_all=df_combined["bln_thn"].to_list()
    #berat_all = df_combined["berat_kg"].to_list()

    berat_2024=data2024["berat_kg"].to_list()
    berat_2025=data2025["berat_kg"].to_list()
    berat_2026=data2026["berat_kg"].to_list()

 
    list_b = [0] * (12 -len(berat_2026))
    berat_2026.extend(list_b)  # to make sure the length matches for plotting

    #st.text(list_b)

   

    from bokeh.models import ColumnDataSource
    from bokeh.plotting import figure, show
    from bokeh.transform import dodge
    from bokeh.models import NumeralTickFormatter, FuncTickFormatter
    from bokeh.models import BoxEditTool, HoverTool

    fruits = bulanku
    years = tahunku

    dataku = {'fruits' : fruits,
        '2024'   : berat_2024,
        '2025'   : berat_2025,
        '2026'   : berat_2026}

    source = ColumnDataSource(dataku)

    hover = HoverTool(
    tooltips=[
        ("Bulan", "@fruits"),
        ("2024", "@2024{0,0}"),
        ("2025", "@2025{0,0}"),
        ("2026", "@2026{0,0}"),],
          #formatters= {'@2024': 'printf', '@2025': 'printf', '@2026': 'printf'}, 
          )



    
    pgab = figure(x_range=fruits, y_range=(0, 200000), title="Volume Berat Kiriman per Bulan Tahun 2024 - 2026",
           height=350, width=1200, toolbar_location=None, )
    

    pgab.vbar(x=dodge('fruits', -0.30, range=pgab.x_range), top='2024', source=source,
       width=0.28, color="#daf3ea", legend_label="2024")

    pgab.vbar(x=dodge('fruits',  0.0,  range=pgab.x_range), top='2025', source=source,
       width=0.28, color="#718dbf", legend_label="2025")

    pgab.vbar(x=dodge('fruits',  0.30, range=pgab.x_range), top='2026', source=source,
       width=0.28, color="#e84d61", legend_label="2026")

    pgab.x_range.range_padding = 0.05
    pgab.xgrid.grid_line_color = None
    pgab.legend.location = "top_left"
    pgab.legend.orientation = "horizontal"
    pgab.yaxis.formatter = NumeralTickFormatter(format="0,0")
    pgab.add_tools(hover)
    #pgab.axis_label_text_font_size = '10px'

    st.bokeh_chart(pgab)

    
    tz_offset = timezone(timedelta(hours=7))  # UTC+7 for Asia/Jakarta
    hari_ini = datetime.now(tz_offset).strftime("%d-%m-%Y | %H:%M:%S")
    st.markdown( f" :green[{hari_ini}] ")





    



   
if selected2=="Review Kinerja":
    page_4()

    query_4="""
    
    SELECT 
    o.bulan,
		now() as waktu,
    o.cabang,
		o.normal_kg,
		o.urgent_kg,
		o.top_urgent_kg,
		o.darat_kg,
    o.outbound_kg_reg,
		o.outbound_kg_mtx,
		o.total_outbound_kg,
		o.trip_trucking,
    i.inbound_kg
FROM
(
    -- Subquery untuk outbound
    SELECT 
        bulan, 
        asal_new AS cabang,
				SUM(CASE WHEN (kdproduk='N' AND reg_mtx='REG')THEN berat ELSE 0 END) AS normal_kg,
				SUM(CASE WHEN (kdproduk='U' AND reg_mtx='REG') THEN berat ELSE 0 END) AS urgent_kg,
				SUM(CASE WHEN (kdproduk='T' AND reg_mtx='REG')THEN berat ELSE 0 END) AS top_urgent_kg,
				SUM(CASE WHEN (kdproduk='D' AND reg_mtx='REG') THEN berat ELSE 0 END) AS darat_kg, 
        SUM(CASE WHEN (kdproduk IN ('N', 'U', 'T', 'D') AND reg_mtx='REG') THEN berat ELSE 0 END) AS outbound_kg_reg,
				sum(case when (kdproduk in ('N', 'U', 'T', 'D') and reg_mtx ='MTX') then berat else 0 end) as outbound_kg_mtx,
				sum(case when kdproduk in ('N', 'U', 'T', 'D') then berat else 0 end) as total_outbound_kg,			
				sum(case when kdproduk='C' then 1 else 0 end) as trip_trucking

    FROM
    (
        -- Data pengiriman keluar
        SELECT 
            DATE_FORMAT(tanggal, "%b-%y") AS bulan, tanggal,
            konid, kdpelanggan,
            pengirim, penerima, tujuan,
            kdproduk, asal, 
            if(left(kdpelanggan,3) in ('CTG','CBK', 'CBO'),'CBH', left(kdpelanggan,3) ) AS asal_new,
						IF(left(kdpelanggan,3)= IF(asal='CBM', 'CBH', asal),'REG','MTX') as reg_mtx,
            koli, berat, kdmani, 
            IF(kdmani IN ('RAX', 'REX', 'CLT', 'SAP'), 'CBD', Kdmani) AS kdmani_new,
            awbno, 
						createdby
        FROM tkonos
        WHERE tanggal >= '2025-09-01' AND tanggal <= NOW()
            AND kdpelanggan NOT LIKE 'CBD18002%'
            and kdpelanggan NOT LIKE 'CSG18002%'
            and kdpelanggan NOT LIKE 'CSB18002%'
            and kdpelanggan NOT LIKE 'CBH17002%'
            and kdpelanggan NOT LIKE 'CML18002%'
            and kdpelanggan NOT LIKE 'CDP18002%'
						#and left(kdpelanggan,3) ='CML'
						#and IF(left(kdpelanggan,3)= IF(asal='CBM', 'CBH', asal),'REG','MTX')='MTX'
            AND left(kdpelanggan,3) IN ('CBH','CBM','CBD', 'CSB', 'CSG', 'CML', 'CDP', 'CBK','CBO','CTG')
    ) AS new1
    GROUP BY bulan, asal_new
		
) AS o
LEFT JOIN
(
    -- Subquery untuk inbound
    SELECT 
        bulan, 
        kdmani_new AS cabang,
        SUM(CASE WHEN kdproduk IN ('N', 'U', 'T', 'D') THEN berat ELSE 0 END) AS inbound_kg
    FROM
    (
        -- Data penerimaan masuk
        SELECT 
            DATE_FORMAT(tanggal, "%b-%y") AS bulan,
            konid, kdpelanggan, nott,           
            jenis, tanggal, pengirim, penerima, tujuan,
            kdproduk, asal, 
            IF(asal='CBM', 'CBH', asal) AS asal_new,
            koli, berat, kdmani,
            IF(kdmani IN ('RAX', 'REX', 'CLT', 'SAP'), 'CBD', 
               IF(kdmani IN ('CBK', 'CBO', 'CTG'), 'CBH', kdmani)) AS kdmani_new,
            awbno, createdby
        FROM tkonos
        WHERE tanggal >= '2025-09-01' AND tanggal <= NOW()
            AND kdpelanggan NOT LIKE 'CBD18002%'
            AND kdpelanggan NOT LIKE 'CSG18002%'
            AND kdpelanggan NOT LIKE 'CSB18002%'
            AND kdpelanggan NOT LIKE 'CBH17002%'
            AND kdpelanggan NOT LIKE 'CML18002%'
            AND kdpelanggan NOT LIKE 'CDP18002%'         
    ) AS new2
    GROUP BY bulan, kdmani_new
) AS i
ON o.bulan = i.bulan AND o.cabang = i.cabang;

            
            
    """

 


    datapage4 = fetch_from_db(query_4, "mysql02")
    datapage4.columns = ['bulan', 'waktu', 'cabang','normal_kg', 'urgent_kg', 'top_urgent_kg', 'darat_kg', 'reg_kg', 'matrix_kg', 'total_kg','trip_trucking', 'inbound_kg']

    datapage4["cabang"] = datapage4[["cabang"]].astype(str)
    datapage4["normal_kg"] = datapage4[["normal_kg"]].astype(int)
    datapage4["urgent_kg"] = datapage4[["urgent_kg"]].astype(int)
    datapage4["top_urgent_kg"] = datapage4[["top_urgent_kg"]].astype(int)
    datapage4["darat_kg"] = datapage4[["darat_kg"]].astype(int)
    datapage4["reg_kg"] = datapage4[["reg_kg"]].astype(int)
    datapage4["total_kg"] = datapage4[["total_kg"]].astype(int)
    datapage4["matrix_kg"] = datapage4[["matrix_kg"]].astype(int)
    datapage4["trip_trucking"] = datapage4[["trip_trucking"]].astype(int)
    datapage4["inbound_kg"] = datapage4[["inbound_kg"]].astype(int)
    #datapage4.style.hide(axis="index")
    
    datapage4= datapage4.drop('waktu', axis=1) # axis=1 specifies column
    datapage4.reset_index(drop=True, inplace=True)
   

    from st_aggrid import AgGrid
    from st_aggrid import AgGrid, GridOptionsBuilder

    
    

   
    lst_cab=datapage4["cabang"].drop_duplicates().sort_index(ascending=True)
    #pilihan4=st.selectbox("Pilih Cabang", lst_cab, key="cabang")  
    
    

    
    col1, col2 = st.columns([2, 10], gap="small")
    col3, col4 = st.columns([10, 2], gap="small")

    with col1:

        #st.text(lst_cab)
        pil_cab=st.selectbox(label="**Pilih Cabang:**",options= lst_cab)

        #st.dataframe(datapage4[[datapage4.cabang==lst_cab]])
        filter_dp4=datapage4[(datapage4.cabang==pil_cab)]

        filter_dp4.reset_index(drop=True, inplace=True)


    with col3:
            
        #st.dataframe(filter_dp4, hide_index=True)
        st.dataframe(filter_dp4.style.hide(axis="index"))
        #st.dataframe(filter_dp4.reset_index(drop=True), hide_index=True)

        #gb = GridOptionsBuilder.from_dataframe(filter_dp4)
        #gb.configure_pagination(paginationAutoPageSize=True) # Add pagination
        #gridOptions = gb.build()    
        #st.dataframe(datapage4, hide_index=True)

        #AgGrid(filter_dp4, gridOptions=gridOptions)


        #AgGrid(filter_dp4, hide_index=True)
        #AgGrid(filter_dp4.reset_index(drop=True), hide_index=True)
           

