import sqlite3
from datetime import date

import pandas as pd
import streamlit as st

DB = "tip.db"


def ket_noi():
    c = sqlite3.connect(DB)
    c.execute(
        """create table if not exists ngay (
            ngay text primary key,
            dau_ngay integer, cuoi_ngay integer, chuyen_khoan integer,
            cod integer, tro_cap integer, phi_giao_hang integer,
            thuong integer, tieu integer, ghi_chu_tieu text,
            mong_muon integer)"""
    )
    return c


def luu(hang):
    with ket_noi() as c:
        c.execute("insert or replace into ngay values (?,?,?,?,?,?,?,?,?,?,?)", hang)


def tai():
    with ket_noi() as c:
        df = pd.read_sql("select * from ngay order by ngay", c)
    if df.empty:
        return df
    df["thu_tu_khach"] = df.cuoi_ngay + df.chuyen_khoan - df.dau_ngay
    df["tip"] = df.thu_tu_khach - df.cod
    df["tong_thu_nhap"] = df.tip + df.tro_cap + df.phi_giao_hang + df.thuong
    df["phan_tram"] = (df.tong_thu_nhap / df.mong_muon.where(df.mong_muon > 0) * 100).round(0)
    df["du_thieu_luy_ke"] = (df.tong_thu_nhap - df.mong_muon).cumsum()
    return df


def dinh_dang(x):
    return f"{x:,.0f}".replace(",", ".")


st.set_page_config(page_title="Theo dõi thu nhập", layout="wide")
st.title("Theo dõi thu nhập")

with st.form("nhap"):
    ngay = st.date_input("Ngày", date.today())
    a, b, c = st.columns(3)
    dau = a.number_input("Tiền đầu ngày", min_value=0, step=1000)
    cuoi = b.number_input("Tiền cuối ngày", min_value=0, step=1000)
    ck = c.number_input("Tiền chuyển khoản", min_value=0, step=1000)
    cod = a.number_input("Tiền COD thực tế", min_value=0, step=1000)
    tro_cap = b.number_input("Trợ cấp", min_value=0, step=1000)
    phi = c.number_input("Phí giao hàng", min_value=0, step=1000)
    thuong = a.number_input("Thưởng", min_value=0, step=1000)
    tieu = b.number_input("Tiêu", min_value=0, step=1000)
    mong_muon = c.number_input("Thu nhập mong muốn", min_value=0, step=1000)
    ghi_chu = st.text_input("Ghi chú tiêu")
    if st.form_submit_button("Lưu"):
        luu((str(ngay), dau, cuoi, ck, cod, tro_cap, phi, thuong, tieu, ghi_chu, mong_muon))
        st.success("Đã lưu")

df = tai()
if df.empty:
    st.info("Chưa có dữ liệu")
    st.stop()

goc = st.sidebar.number_input("Mốc tiền ban đầu", value=0, step=1000)
st.sidebar.metric("Tổng Tiền", dinh_dang(goc + df.tong_thu_nhap.sum() - df.tieu.sum()))

df["thang"] = df.ngay.str[:7]
thang = st.selectbox("Tháng", sorted(df.thang.unique(), reverse=True))
m = df[df.thang == thang]
tong = m.tong_thu_nhap.sum()
mm = m.mong_muon.sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Tổng thu nhập", dinh_dang(tong))
k2.metric("Tổng tiêu", dinh_dang(m.tieu.sum()))
k3.metric("Tổng mong muốn", dinh_dang(mm))
k4.metric("% đạt được", f"{tong / mm * 100:.0f}%" if mm else "-")

st.dataframe(m.drop(columns="thang"))
st.line_chart(df.set_index("ngay")["du_thieu_luy_ke"])