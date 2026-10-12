import csv
import io

from flask import (Flask, jsonify, render_template_string, request, abort,
                   redirect, url_for, make_response)

app = Flask(__name__)
app.json.ensure_ascii = False  # JSON tiếng Việt có dấu

STUDENTS = {
    "23T1020001": {"name": "Nguyễn Văn An", "lop": "K47A",
                   "scores": {"PMMNM": 8.5, "CSDL": 7.0, "MMT": 9.0}},
    "23T1020002": {"name": "Trần Thị Bình", "lop": "K47A",
                   "scores": {"PMMNM": 6.0, "CSDL": 5.5, "MMT": 7.0}},
    "23T1020003": {"name": "Lê Hoàng Cường", "lop": "K47B",
                   "scores": {"PMMNM": 9.5, "CSDL": 9.0}},
    "23T1020004": {"name": "Phạm Minh Dũng", "lop": "K47B",
                   "scores": {"PMMNM": 4.0, "CSDL": 3.5, "MMT": 5.0}},
    "23T1020005": {"name": "Hoàng Thu Hà", "lop": "K47A",
                   "scores": {}},
    "23T1020006": {"name": "Võ Quốc Khánh", "lop": "K47C",
                   "scores": {"PMMNM": 7.5, "MMT": 8.0}},
}


def tinh_diem_tb(scores):
    if not scores:
        return None
    return round(sum(scores.values()) / len(scores), 2)


def xep_loai(dtb):
    if dtb is None:
        return "Chưa có điểm"
    if dtb >= 9.0:
        return "Xuất sắc"
    if dtb >= 8.0:
        return "Giỏi"
    if dtb >= 7.0:
        return "Khá"
    if dtb >= 5.0:
        return "Trung bình"
    return "Yếu"


def ds_lop():
    """Danh sách lớp không trùng, lấy từ dữ liệu."""
    return sorted({sv["lop"] for sv in STUDENTS.values()})


INDEX_HTML = """
<h1>Quản lý điểm sinh viên</h1>
<p>Tổng số sinh viên: {{ tong_sv }}</p>
<p>Số lớp: {{ so_lop }}</p>
<p><a href="{{ url_for('student_list') }}">/students</a> | <a href="{{ url_for('api_students') }}">/api/students</a></p>
"""

STUDENTS_HTML = """
<h1>Danh sách sinh viên</h1>
<p>
  {% if lop_chon %}<a href="{{ url_for('student_list') }}">Tất cả</a>{% else %}<b>Tất cả</b>{% endif %}
  {% for l in cac_lop %}
    | {% if l == lop_chon %}<b>{{ l }}</b>{% else %}<a href="{{ url_for('student_list', lop=l) }}">{{ l }}</a>{% endif %}
  {% endfor %}
</p>
{% if students %}
<table border="1" cellpadding="6">
  <tr><th>MSSV</th><th>Họ tên</th><th>Lớp</th><th>Điểm TB</th><th>Xếp loại</th></tr>
  {% for s in students %}
  <tr>
    <td><a href="{{ url_for('student_detail', mssv=s.mssv) }}">{{ s.mssv }}</a></td>
    <td>{{ s.name }}</td>
    <td>{{ s.lop }}</td>
    <td>{{ s.dtb if s.dtb is not none else '-' }}</td>
    <td>{{ s.xep_loai }}</td>
  </tr>
  {% endfor %}
</table>
{% else %}
<p>Không có sinh viên phù hợp</p>
{% endif %}
"""

DETAIL_HTML = """
<h1>Chi tiết sinh viên</h1>
<p>Họ tên: {{ sv.name }}</p>
<p>MSSV: {{ mssv }}</p>
<p>Lớp: <a href="{{ url_for('student_list', lop=sv.lop) }}">{{ sv.lop }}</a></p>
<p>Điểm TB: {{ dtb if dtb is not none else '-' }}</p>
<p>Xếp loại: {{ loai }}</p>

<h2>Bảng điểm từng học phần</h2>
{% if sv.scores %}
<table border="1" cellpadding="6">
  <tr><th>Học phần</th><th>Điểm</th></tr>
  {% for mon, diem in sv.scores.items() %}
  <tr><td>{{ mon }}</td><td>{{ diem }}</td></tr>
  {% endfor %}
</table>
{% else %}
<p>Chưa có điểm</p>
{% endif %}
<p><a href="{{ url_for('student_export', mssv=mssv) }}">Tải bảng điểm (CSV)</a></p>
<p>Link rút gọn: <a href="{{ url_for('student_short', mssv=mssv) }}">{{ url_for('student_short', mssv=mssv, _external=True) }}</a></p>
<p><a href="{{ url_for('student_list') }}">← Danh sách sinh viên</a></p>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML, tong_sv=len(STUDENTS),
                                  so_lop=len(ds_lop()))


@app.route("/students")
def student_list():
    lop_param = request.args.get("lop", "").strip()
    cac_lop = ds_lop()
    lop_chon = next((l for l in cac_lop if l.lower() == lop_param.lower()), None)

    rows = []
    for mssv, sv in STUDENTS.items():
        if lop_param and sv["lop"].lower() != lop_param.lower():
            continue
        dtb = tinh_diem_tb(sv["scores"])
        rows.append({"mssv": mssv, "name": sv["name"], "lop": sv["lop"],
                     "dtb": dtb, "xep_loai": xep_loai(dtb)})

    return render_template_string(STUDENTS_HTML, students=rows,
                                  cac_lop=cac_lop, lop_chon=lop_chon)


@app.route("/students/<mssv>")
def student_detail(mssv):
    sv = STUDENTS.get(mssv)
    if sv is None:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    dtb = tinh_diem_tb(sv["scores"])
    return render_template_string(DETAIL_HTML, mssv=mssv, sv=sv,
                                  dtb=dtb, loai=xep_loai(dtb))


@app.route("/sv/<mssv>")
def student_short(mssv):
    """Link rút gọn: chuyển hướng vĩnh viễn (301) tới trang chi tiết."""
    return redirect(url_for("student_detail", mssv=mssv), code=301)


@app.route("/students/<mssv>/export")
def student_export(mssv):
    sv = STUDENTS.get(mssv)
    if sv is None:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")

    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["hoc_phan", "diem"])
    for mon, diem in sv["scores"].items():
        writer.writerow([mon, diem])

    resp = make_response(buf.getvalue())
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = f"attachment; filename=diem_{mssv}.csv"
    return resp


@app.route("/api/students")
def api_students():
    return jsonify(STUDENTS)


if __name__ == "__main__":
    app.run(debug=True, port=8000)