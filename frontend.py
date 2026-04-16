import dash
from dash import dcc, html, Input, Output, State, callback, MATCH, ALL
import dash_bootstrap_components as dbc
import requests
import base64
import os
import json

API_URL = "http://127.0.0.1:8000"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG], suppress_callback_exceptions=True)
app.title = "AI Resume Platform"

# --- Navigation Bar ---
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Student Portal", href="/")),
        dbc.NavItem(dbc.NavLink("Check Result", href="/student-result")),
        dbc.NavItem(dbc.NavLink("HR Dashboard", href="/hr")),
    ],
    brand="Resume Engine",
    brand_href="/",
    color="primary",
    dark=True,
    className="mb-4"
)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='hr-auth-store', storage_type='session'),
    navbar,
    dbc.Container(id='page-content', className="py-2")
])

# --- Helper functions ---
def build_score_card(title, score, max_score):
    percentage = (score / max_score) * 100 if max_score > 0 else 0
    color = "success" if percentage >= 80 else "warning" if percentage >= 50 else "danger"
    return html.Div([
        html.Div(f"{title}", className="fw-bold mb-1", style={"fontSize": "14px"}),
        dbc.Progress(value=percentage, color=color, className="mb-1", style={"height": "10px"}),
        html.Div(f"{score} / {max_score}", className="text-end text-muted", style={"fontSize": "12px"})
    ], className="mb-3")

def create_results_layout(data):
    overall = data.get("overall_score", 0)
    overall_color = "success" if overall >= 80 else "warning" if overall >= 60 else "danger"
    breakdown = data.get("breakdown", {})
    
    scores_col = dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.H4("Overall AI Score", className="text-center text-muted"),
                html.H1(f"{overall}%", className=f"text-center text-{overall_color} fw-bold display-4"),
                html.Hr(),
                html.H5("Skill Breakdown", className="mb-3"),
                build_score_card("Technical Skills", breakdown.get("technical_skills", {}).get("score", 0), breakdown.get("technical_skills", {}).get("max", 30)),
                build_score_card("Projects", breakdown.get("projects", {}).get("score", 0), breakdown.get("projects", {}).get("max", 25)),
                build_score_card("Innovation", breakdown.get("innovation", {}).get("score", 0), breakdown.get("innovation", {}).get("max", 20)),
                build_score_card("Experience & Academics", breakdown.get("experience_academics", {}).get("score", 0), breakdown.get("experience_academics", {}).get("max", 10)),
                build_score_card("Resume Clarity", breakdown.get("resume_clarity", {}).get("score", 0), breakdown.get("resume_clarity", {}).get("max", 10)),
                build_score_card("Leadership", breakdown.get("leadership", {}).get("score", 0), breakdown.get("leadership", {}).get("max", 5)),
            ])
        ], className="shadow bg-dark border-secondary h-100")
    ], md=4)
    
    strengths = [html.Li(s) for s in data.get("strengths", [])]
    weaknesses = [html.Li(w) for w in data.get("weak_areas", [])]
    
    feedback_col = dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.H4("Analysis Feedback", className="mb-4 text-info"),
                dbc.Row([
                    dbc.Col([html.H6("Strengths", className="text-success"), html.Ul(strengths, className="text-light", style={"opacity": "0.9"})], md=6),
                    dbc.Col([html.H6("Areas for Improvement", className="text-warning"), html.Ul(weaknesses, className="text-light", style={"opacity": "0.9"})], md=6)
                ]),
                html.Hr(),
                html.H6("AI Selection Chances", className="text-muted"),
                html.H5(data.get("selection_chances", "N/A"), className="text-primary"),
                html.P(data.get("selection_reason", ""), className="text-light mb-4", style={"fontSize": "15px"}),
                html.Div([
                    html.H6("Final AI Verdict", className="text-light"),
                    html.P(data.get("final_verdict", ""), className="fst-italic text-secondary")
                ], className="p-3 bg-black rounded border border-dark")
            ])
        ], className="shadow bg-dark border-secondary h-100")
    ], md=8)
    
    return dbc.Row([scores_col, feedback_col], className="mt-4 gx-4")

def render_status_badge(status):
    color = "secondary"
    if status == "approved": color = "success"
    elif status == "rejected": color = "danger"
    return dbc.Badge(status.upper(), color=color, className="fs-5 p-2 mb-3")

# --- Layouts ---

# 1. Student Upload Layout
layout_student_upload = html.Div([
    html.H2("Submit Application", className="text-center mb-4"),
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dbc.Input(id="stu-name", placeholder="Full Name", type="text", className="mb-3"), md=6),
                dbc.Col(dbc.Input(id="stu-email", placeholder="Email Address", type="email", className="mb-3"), md=6),
            ]),
            dbc.Row([
                dbc.Col(dbc.Input(id="stu-phone", placeholder="Phone Number", type="text", className="mb-3"), md=6),
                dbc.Col(dbc.Input(id="stu-college", placeholder="College/University", type="text", className="mb-3"), md=6),
            ]),
            dbc.Row([
                dbc.Col(dbc.Input(id="stu-branch", placeholder="Branch/Major", type="text", className="mb-3"), md=6),
                dbc.Col(dbc.Input(id="stu-year", placeholder="Year of Study", type="text", className="mb-3"), md=6),
            ]),
            dcc.Upload(
                id='upload-resume',
                children=html.Div(['Drag and Drop or ', html.A('Select Resume File', className="text-info")]),
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '2px', 
                    'borderStyle': 'dashed', 'borderRadius': '10px', 'borderColor': '#0dcaf0', 
                    'textAlign': 'center', 'cursor': 'pointer', 'backgroundColor': 'rgba(13, 202, 240, 0.05)',
                    'marginBottom': '20px'
                },
                multiple=False, accept=".pdf, .png, .jpg, .jpeg, .doc, .docx"
            ),
            html.Div(id="upload-filename", className="text-success mb-3 fst-italic"),
            dbc.Button("Submit Application", id="btn-submit", color="primary", className="w-100", size="lg")
        ])
    ], className="bg-dark border-secondary shadow mx-auto", style={"maxWidth": "800px"}),
    html.Div(id="submit-status", className="text-center mt-4"),
    dcc.Loading(id="loading-submit", type="circle", children=html.Div(id="submit-result-area"))
])

# 2. Student Result Layout
layout_student_result = html.Div([
    html.H2("Check Application Status", className="text-center mb-4"),
    dbc.InputGroup([
        dbc.Input(id="input-sub-id", placeholder="Enter your Submission ID...", type="text"),
        dbc.Button("Check Status", id="btn-check-status", color="primary"),
    ], className="mb-5 mx-auto", style={"maxWidth": "600px"}),
    dcc.Loading(id="loading-status", type="circle", children=html.Div(id="status-result-area"))
])

# 3. HR Dashboard
layout_hr_dashboard = html.Div([
    html.H2("HR Dashboard", className="mb-4"),
    dbc.InputGroup([
        dbc.InputGroupText("HR Auth Key"),
        dbc.Input(id="hr-api-key", type="password", placeholder="Enter X-HR-KEY...", value="secret_hr_123"),
        dbc.Button("Load Submissions", id="btn-load-hr", color="primary")
    ], className="mb-4", style={"maxWidth": "500px"}),
    
    dbc.RadioItems(
        options=[
            {"label": "All", "value": "all"},
            {"label": "Pending", "value": "pending"},
            {"label": "Approved", "value": "approved"},
            {"label": "Rejected", "value": "rejected"},
        ],
        value="all", id="hr-filter", inline=True, className="mb-4"
    ),
    dcc.Loading(id="loading-hr-list", type="circle", children=html.Div(id="hr-list-area"))
])

# 4. HR Detail View
layout_hr_detail = html.Div([
    html.Div(id="hr-detail-area"),
    dcc.Location(id="hr-detail-redirect", refresh=True)
])


# --- Router ---
@callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/':
        return layout_student_upload
    elif pathname == '/student-result':
        return layout_student_result
    elif pathname == '/hr':
        return layout_hr_dashboard
    elif pathname and pathname.startswith('/hr/view/'):
        return layout_hr_detail
    else:
        return html.H1("404 - Page Not Found", className="text-center text-danger mt-5")

# --- Callbacks ---

# Upload UI update
@callback(Output("upload-filename", "children"), Input("upload-resume", "filename"))
def update_filename(filename):
    if filename: return f"File selected: {filename}"
    return ""

# Submission logic
@callback(
    Output("submit-result-area", "children"),
    Output("submit-status", "children"),
    Input("btn-submit", "n_clicks"),
    State("stu-name", "value"), State("stu-email", "value"), State("stu-phone", "value"),
    State("stu-college", "value"), State("stu-branch", "value"), State("stu-year", "value"),
    State("upload-resume", "contents"), State("upload-resume", "filename"),
    prevent_initial_call=True
)
def handle_submission(n_clicks, name, email, phone, college, branch, year, contents, filename):
    if not all([name, email, phone, college, branch, year, contents]):
        return "", html.Div("Please fill out all fields and select a file.", className="text-danger")
    try:
        content_type, content_string = contents.split(',')
        mime_type = content_type.split(':')[1].split(';')[0]
        file_bytes = base64.b64decode(content_string)
        
        data = {
            "student_name": name, "student_email": email, "phone": phone,
            "college": college, "branch": branch, "year_of_study": year
        }
        files = {'file': (filename, file_bytes, mime_type)}
        
        res = requests.post(f"{API_URL}/submit", data=data, files=files)
        if res.status_code == 200:
            res_json = res.json()
            sub_id = res_json.get("submission_id")
            return [
                html.Div([
                    html.H4("Application Submitted Successfully!", className="text-success text-center"),
                    html.H5(f"Your Submission ID: {sub_id}", className="text-center text-info mb-4"),
                    html.P("Please save this ID securely. You will need it to check your HR decision.", className="text-center text-muted"),
                    create_results_layout(res_json.get("ai_result", {}))
                ])
            ], ""
        else:
            return "", html.Div(f"Error {res.status_code}: {res.text}", className="text-danger")
    except Exception as e:
        return "", html.Div(f"Error: {e}", className="text-danger")

# Check status logic
@callback(
    Output("status-result-area", "children"),
    Input("btn-check-status", "n_clicks"),
    State("input-sub-id", "value"),
    prevent_initial_call=True
)
def check_status(n_clicks, sub_id):
    if not sub_id: return html.Div("Please enter an ID.", className="text-danger text-center")
    try:
        res = requests.get(f"{API_URL}/student/result/{sub_id.strip()}")
        if res.status_code == 200:
            doc = res.json()
            remarks = doc.get("hr_remarks")
            return html.Div([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"Applicant: {doc.get('student_name')}", className="text-info"),
                        render_status_badge(doc.get("status")),
                        html.Div([
                            html.H6("HR Remarks:"),
                            html.P(remarks, className="text-light fst-italic p-2 bg-black rounded border border-secondary")
                        ], className="mt-3") if remarks else html.Div()
                    ])
                ], className="bg-dark mb-4 shadow"),
                create_results_layout(doc.get("ai_result", {}))
            ])
        else:
            return html.Div("Submission not found or invalid ID.", className="text-danger text-center")
    except Exception as e:
        return html.Div(f"Error: {e}", className="text-danger text-center")

# HR Dashboard Load
@callback(
    Output("hr-list-area", "children"),
    Output("hr-auth-store", "data"),
    Input("btn-load-hr", "n_clicks"),
    Input("hr-filter", "value"),
    State("hr-api-key", "value")
)
def load_hr_dashboard(n_clicks, filter_val, api_key):
    try:
        current_key = api_key or ""
        headers = {"X-HR-KEY": current_key}
        url = f"{API_URL}/hr/submissions"
        if filter_val != "all":
            url += f"?status={filter_val}"
        
        res = requests.get(url, headers=headers)
        if res.status_code == 403:
            return html.Div("Access Denied: Invalid HR Key", className="text-danger"), None
        elif res.status_code != 200:
            return html.Div(f"Error {res.status_code}", className="text-danger"), current_key
            
        docs = res.json()
        if not docs:
            return html.Div("No submissions found.", className="text-muted text-center mt-5"), current_key
            
        table_header = [
            html.Thead(html.Tr([
                html.Th("Name"), html.Th("College"), html.Th("AI Score"), html.Th("Status"), html.Th("Action")
            ]))
        ]
        
        rows = []
        for d in docs:
            st = d.get('status', 'pending')
            color = "secondary"
            if st == "approved": color = "success"
            elif st == "rejected": color = "danger"
            
            rows.append(html.Tr([
                html.Td(d.get("student_name")),
                html.Td(d.get("college")),
                html.Td(f"{d.get('ai_score')}%"),
                html.Td(dbc.Badge(st.upper(), color=color)),
                html.Td(dbc.Button("Review", href=f"/hr/view/{d.get('id')}", size="sm", color="info", outline=True))
            ]))
            
        table_body = [html.Tbody(rows)]
        return dbc.Table(table_header + table_body, striped=True, bordered=True, hover=True, color="dark"), current_key
        
    except Exception as e:
        return html.Div(f"Error: {e}", className="text-danger"), dash.no_update

# HR Detail Page Load
@callback(
    Output("hr-detail-area", "children"),
    Input("url", "pathname"),
    State("hr-auth-store", "data")
)
def load_hr_detail(pathname, api_key):
    if not pathname or not pathname.startswith('/hr/view/'):
        return dash.no_update
        
    sub_id = pathname.split('/')[-1]
    headers = {"X-HR-KEY": api_key or "secret_hr_123"}
    try:
        res = requests.get(f"{API_URL}/hr/submission/{sub_id}", headers=headers)
        if res.status_code != 200:
            return html.Div(f"Error fetching record {res.status_code}", className="text-danger")
        doc = res.json()
        
        return html.Div([
            dbc.Button("← Back to Dashboard", href="/hr", color="link", className="mb-4 ps-0 text-info"),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3(doc.get("student_name"), className="text-primary fw-bold"),
                            html.Hr(),
                            html.P([html.Strong("Email: "), doc.get("student_email")]),
                            html.P([html.Strong("Phone: "), doc.get("phone")]),
                            html.P([html.Strong("College: "), doc.get("college")]),
                            html.P([html.Strong("Branch: "), doc.get("branch")]),
                            html.P([html.Strong("Year: "), doc.get("year_of_study")]),
                            html.Br(),
                            html.H5("Current Status", className="text-muted"),
                            render_status_badge(doc.get("status"))
                        ])
                    ], className="bg-dark shadow h-100")
                ], md=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("HR Decision Panel", className="text-warning mb-3"),
                            dbc.Textarea(id="hr-remarks-input", placeholder="Enter remarks/reasoning here...", value=doc.get("hr_remarks") or "", style={"height": "120px"}, className="mb-3 bg-black text-light border-secondary"),
                            dbc.Row([
                                dbc.Col(dbc.Button("Approve Candidate", id={"type": "btn-decision", "action": "approved"}, color="success", className="w-100")),
                                dbc.Col(dbc.Button("Reject Candidate", id={"type": "btn-decision", "action": "rejected"}, color="danger", className="w-100"))
                            ]),
                            html.Div(id="decision-status", className="mt-3")
                        ])
                    ], className="bg-dark shadow h-100")
                ], md=8)
            ], className="mb-4 align-items-stretch"),
            html.H3("AI Processing Summary", className="mb-3 mt-5"),
            create_results_layout(doc.get("ai_result", {}))
        ])
    except Exception as e:
        return html.Div(f"Error: {e}")

# Process HR Decision
@callback(
    Output("decision-status", "children"),
    Input({"type": "btn-decision", "action": ALL}, "n_clicks"),
    State("url", "pathname"),
    State("hr-remarks-input", "value"),
    State("hr-auth-store", "data"),
    prevent_initial_call=True
)
def process_decision(n_clicks_list, pathname, remarks, api_key):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
        
    action_type = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])['action']
    sub_id = pathname.split('/')[-1]
    
    headers = {"X-HR-KEY": api_key or "secret_hr_123"}
    data = {"status": action_type, "hr_remarks": remarks or ""}
    
    try:
        res = requests.patch(f"{API_URL}/hr/submission/{sub_id}/decision", json=data, headers=headers)
        if res.status_code == 200:
            return html.Div(f"Successfully {action_type}! Reloading...", className="text-success")
        else:
            return html.Div(f"Error {res.status_code}: {res.text}", className="text-danger")
    except Exception as e:
        return html.Div(f"Error: {e}", className="text-danger")


if __name__ == '__main__':
    app.run(debug=True, port=8050)
