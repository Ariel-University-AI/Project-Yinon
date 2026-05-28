from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os

OUTPUT = "AG_Project_Summary.pdf"

BLUE      = (28,  78, 128)
DARK_BLUE = (15,  50,  90)
LIGHT_BG  = (240, 246, 255)
ACCENT    = (52, 152, 219)
GREEN     = (39, 174,  96)
ORANGE    = (230, 126,  34)
GREY_TEXT = (80, 80, 80)
WHITE     = (255, 255, 255)
LIGHT_GREY= (245, 245, 245)
MID_GREY  = (200, 200, 200)

class PDF(FPDF):
    def header(self):
        pass

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-14)
        self.set_draw_color(*MID_GREY)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), 195, self.get_y())
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GREY_TEXT)
        self.cell(0, 6, f"Smart Real Estate Advisor  |  Page {self.page_no() - 1}", align="C")

    def cover(self):
        # Background
        self.set_fill_color(*DARK_BLUE)
        self.rect(0, 0, 210, 297, "F")

        # Decorative band
        self.set_fill_color(*ACCENT)
        self.rect(0, 120, 210, 5, "F")
        self.rect(0, 128, 210, 2, "F")

        # Subtitle bar
        self.set_fill_color(*BLUE)
        self.rect(0, 100, 210, 40, "F")

        # Title
        self.set_y(42)
        self.set_font("Helvetica", "B", 36)
        self.set_text_color(*WHITE)
        self.cell(0, 14, "Smart Real Estate", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(0, 14, "Investment Advisor", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Hebrew subtitle
        self.set_y(82)
        self.set_font("Helvetica", "", 16)
        self.set_text_color(*ACCENT)
        self.cell(0, 9, "Yoetz Nadlan Chacham", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Description block
        self.set_y(108)
        self.set_font("Helvetica", "", 12)
        self.set_text_color(*WHITE)
        self.cell(0, 8, "ML-Powered Real Estate Analytics for the Israeli Market", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Info block
        self.set_y(155)
        for label, value in [
            ("Course", "Mathematical Geodesy - Ariel University"),
            ("Dataset", "10,424 Transactions  |  Israel Tax Authority"),
            ("Model", "XGBoost  |  R2 = 0.741  |  RMSE ~ 607,000 ILS"),
            ("Stack", "Python  |  Streamlit  |  scikit-learn  |  XGBoost"),
            ("Date", "May 2026"),
        ]:
            self.set_x(40)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*ACCENT)
            self.cell(42, 8, label + ":", align="L")
            self.set_font("Helvetica", "", 10)
            self.set_text_color(*WHITE)
            self.cell(0, 8, value, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Bottom line
        self.set_y(265)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(*MID_GREY)
        self.cell(0, 6, "Prepared with Claude Code  |  Anthropic", align="C")

    def section_title(self, number, title, color=BLUE):
        self.ln(4)
        self.set_fill_color(*color)
        self.rect(15, self.get_y(), 4, 10, "F")
        self.set_x(22)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*color)
        self.cell(0, 10, f"{number}.  {title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*color)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(3)

    def body_text(self, text, indent=0):
        self.set_x(15 + indent)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*GREY_TEXT)
        self.multi_cell(180 - indent, 5.5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def bullet(self, text, indent=6):
        self.set_x(15 + indent)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*ACCENT)
        self.cell(5, 5.5, chr(149))
        self.set_text_color(*GREY_TEXT)
        self.multi_cell(174 - indent, 5.5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def info_box(self, title, lines, bg=LIGHT_BG, title_color=BLUE):
        self.set_fill_color(*bg)
        start_y = self.get_y()
        box_h = 8 + len(lines) * 6 + 4
        self.rect(15, start_y, 180, box_h, "F")
        self.set_draw_color(*title_color)
        self.set_line_width(0.5)
        self.line(15, start_y, 15, start_y + box_h)
        self.set_xy(20, start_y + 3)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*title_color)
        self.cell(0, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        for line in lines:
            self.set_x(20)
            self.set_font("Helvetica", "", 9.5)
            self.set_text_color(*GREY_TEXT)
            self.cell(0, 6, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def metrics_row(self, metrics):
        box_w = 180 / len(metrics)
        start_x = 15
        start_y = self.get_y()
        for label, value, sub in metrics:
            self.set_fill_color(*LIGHT_BG)
            self.rect(start_x, start_y, box_w - 2, 22, "F")
            self.set_draw_color(*ACCENT)
            self.set_line_width(0.4)
            self.line(start_x, start_y, start_x, start_y + 22)
            self.set_xy(start_x + 2, start_y + 2)
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(*BLUE)
            self.cell(box_w - 4, 7, value, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_x(start_x + 2)
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*GREY_TEXT)
            self.cell(box_w - 4, 5, label, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_x(start_x + 2)
            self.set_font("Helvetica", "I", 7.5)
            self.set_text_color(*ACCENT)
            self.cell(box_w - 4, 5, sub, align="C")
            start_x += box_w
        self.ln(26)

    def table(self, headers, rows, col_widths):
        # Header row
        self.set_fill_color(*BLUE)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 9)
        self.set_x(15)
        for h, w in zip(headers, col_widths):
            self.cell(w, 8, h, border=0, fill=True, align="C")
        self.ln()
        # Data rows
        for i, row in enumerate(rows):
            self.set_fill_color(*LIGHT_GREY if i % 2 == 0 else WHITE)
            self.set_text_color(*GREY_TEXT)
            self.set_font("Helvetica", "", 9)
            self.set_x(15)
            for cell, w in zip(row, col_widths):
                self.cell(w, 7, str(cell), border=0, fill=True, align="C")
            self.ln()
        self.ln(3)

    def flow_box(self, x, y, w, h, text, fill=LIGHT_BG, text_color=BLUE, bold=False):
        self.set_fill_color(*fill)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.3)
        self.rect(x, y, w, h, "FD")
        self.set_xy(x, y + (h - 6) / 2)
        self.set_font("Helvetica", "B" if bold else "", 9)
        self.set_text_color(*text_color)
        self.cell(w, 6, text, align="C")

    def arrow(self, x1, y1, x2, y2):
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.5)
        self.line(x1, y1, x2, y2)
        # arrowhead
        self.line(x2, y2, x2 - 2, y2 - 2)
        self.line(x2, y2, x2 + 2, y2 - 2)


# ??????????????????????????????????????????????????????????????????????????????

pdf = PDF()
pdf.set_margins(15, 15, 15)
pdf.set_auto_page_break(True, margin=18)

# ?? COVER ????????????????????????????????????????????????????????????????????
pdf.add_page()
pdf.cover()

# ?? PAGE 2: OVERVIEW ?????????????????????????????????????????????????????????
pdf.add_page()
pdf.section_title("1", "Project Overview")
pdf.body_text(
    "The Smart Real Estate Investment Advisor is a data-driven platform designed to help "
    "Israeli real estate investors identify promising settlements and undervalued deals. "
    "It combines transaction data from Israel's Tax Authority with socioeconomic indices "
    "from the Central Bureau of Statistics (CBS/LAMAS), trains a machine learning model "
    "to predict fair apartment prices, and serves a Streamlit web application that scores "
    "and ranks settlements based on the investor's profile."
)

pdf.section_title("2", "The Core Idea")
pdf.body_text(
    "The platform is built around one central insight: if the ML model predicts an apartment "
    "should sell for X, but it actually sold for less - that is a potential investment opportunity. "
    "By aggregating this 'price gap' across all deals in a settlement, combined with price trends "
    "and market liquidity, the app produces a Viability Score (0-100) for each settlement."
)
pdf.info_box("Viability Score Formula", [
    "Current Yield goal:   60% price gap  +  20% price trend  +  20% liquidity",
    "Appreciation goal:    30% price gap  +  50% price trend  +  20% liquidity",
    "Positive gap = property sold below model prediction = potential opportunity",
])

pdf.section_title("3", "Tech Stack")
pdf.table(
    ["Layer", "Technology", "Purpose"],
    [
        ["Data Collection",   "Python + requests + pyproj",  "GovMap API scraping + coordinate transforms"],
        ["Data Processing",   "pandas + numpy",               "Cleaning, filtering, feature engineering"],
        ["Machine Learning",  "XGBoost + scikit-learn",       "Price prediction model"],
        ["Model Storage",     "joblib",                        "Serialize & load model.pkl"],
        ["Web App",           "Streamlit",                     "Interactive investment dashboard"],
        ["Socioeconomic Data","CBS / LAMAS",                   "Settlement-level index enrichment"],
    ],
    [38, 60, 82]
)

# ?? PAGE 3: DATA PIPELINE ????????????????????????????????????????????????????
pdf.add_page()
pdf.section_title("4", "Data Pipeline")
pdf.body_text(
    "The data flows through four sequential stages before reaching the model and app:"
)

# Flow diagram
base_y = pdf.get_y() + 2
bw, bh, gap = 34, 14, 6
starts = [15, 15 + bw + gap, 15 + 2*(bw + gap), 15 + 3*(bw + gap), 15 + 4*(bw + gap)]
labels = ["ALL_DATA\n.xlsx", "clean_\ndata.py", "prepare_\nml_data.py", "train_\nmodel.py", "app.py"]
fills  = [LIGHT_BG, LIGHT_BG, LIGHT_BG, LIGHT_BG, BLUE]
tcolors= [BLUE,     BLUE,     BLUE,     BLUE,      WHITE]

for i, (sx, lbl, fill, tc) in enumerate(zip(starts, labels, fills, tcolors)):
    pdf.flow_box(sx, base_y, bw, bh, lbl.replace("\n", " "), fill, tc, bold=(i == 4))
    if i < len(starts) - 1:
        ax = sx + bw
        pdf.arrow(ax, base_y + bh / 2, ax + gap, base_y + bh / 2)

pdf.set_y(base_y + bh + 6)

pdf.info_box("Stage 1 - nadlan_loader.py: Data Collection", [
    "Scrapes GovMap API (govmap.gov.il) across 20 ITM coordinate bounding boxes covering Israel.",
    "Collects up to 10,000 transactions: max 80 per city, max 3 per building.",
    "Guarantees at least 25% of each city's deals are from 2025+ (recency requirement).",
    "Converts coordinates: ITM (EPSG:2039) <-> Web Mercator (EPSG:3857) using pyproj.",
    "Output: raw deal data with polygon IDs, deal dates, prices, and geocoordinates.",
])

pdf.info_box("Stage 2 - clean_data.py: Outlier Removal", [
    "Loads ALL_DATA (1).xlsx from the Israel Tax Authority.",
    "Removes deals with price < 100,000 ILS or > 10,000,000 ILS.",
    "Removes properties with area < 20 m2 or > 500 m2.",
    "Output: all_data_clean.csv",
])

pdf.info_box("Stage 3 - prepare_ml_data.py: Feature Engineering", [
    "Filters out non-residential types: offices, stores, warehouses, industrial, agricultural, etc.",
    "Parses dealDate into deal_year and deal_month numeric features.",
    "Maps Hebrew floor names to integers (basement=-1, ground=0, first=1, ...).",
    "Fills missing rooms / floor / socio values with column medians.",
    "Label-encodes settlement, deal nature, and neighborhood as category codes.",
    "Target-encodes street names: each street replaced by its mean sale price.",
    "Saves apartments_ml_ready.csv (for model) and apartments_display.csv (for UI).",
])

# ?? PAGE 4: LAMAS + BAT YAM ??????????????????????????????????????????????????
pdf.add_page()
pdf.section_title("5", "Socioeconomic Data - LAMAS_EDA_2M")
pdf.body_text(
    "Israel's Central Bureau of Statistics (CBS) publishes a socioeconomic index for every "
    "locality, ranking it across 10 clusters based on income, education, employment, and "
    "demographics. This index is merged into every transaction as the feature 'socio_index_avg', "
    "and is used in the app to separate established markets (high index) from emerging ones."
)
pdf.table(
    ["Part", "Script", "Purpose", "Output"],
    [
        ["Part 1", "gen_eda.py",        "Interactive EDA dashboard",        "eda.html, data_preview.html"],
        ["Part 1", "gen_eda_app.py",    "App-style EDA with cluster filter", "eda_app.html"],
        ["Part 2", "clean_missing.py",  "Impute missing values (mean/mode)", "-"],
        ["Part 2", "check_duplicates.py","Identify and report duplicates",   "missing_report.html"],
        ["Part 3", "gen_eda_final.py",  "Final cleaned analysis",           "DATA_final.csv, eda_final.html"],
    ],
    [18, 48, 70, 44]
)
pdf.body_text(
    "Features in the socioeconomic dataset include: socioeconomic cluster (1-10), "
    "average schooling years, % with academic degree, employment rate, income distribution "
    "percentiles, average days abroad, vehicles per 100 residents, and age/dependency ratios."
)

pdf.section_title("6", "Bat Yam Case Study - DATA_FILES/BATYAM_2M")
pdf.body_text(
    "Before scaling the pipeline to all of Israel, Bat Yam was used as a single-city prototype "
    "to validate the entire workflow end-to-end: data collection, cleaning, EDA, and analysis."
)
pdf.table(
    ["File", "Purpose"],
    [
        ["clean_bat_yam.py",      "Filters nadlan_final.csv to Bat Yam only, cleans and reports"],
        ["gen_bat_yam_eda.py",    "Generates EDA HTML report for Bat Yam transactions"],
        ["gen_nadlan_preview.py", "HTML preview of the raw nadlan data"],
        ["analyze_area.py",       "Area-level statistics and analysis"],
        ["bat_yam_clean.csv",     "Cleaned Bat Yam transaction dataset"],
        ["bat_yam_eda.html",      "Interactive EDA dashboard for Bat Yam"],
    ],
    [70, 110]
)

# ?? PAGE 5: MODEL ?????????????????????????????????????????????????????????????
pdf.add_page()
pdf.section_title("7", "Machine Learning Model - train_model.py")
pdf.body_text(
    "An XGBoost Regressor is trained to predict apartment sale prices (dealAmount) from "
    "engineered features. The model is serialized to model.pkl and loaded at app startup "
    "to run predictions on all apartments in the dataset."
)

pdf.metrics_row([
    ("Training rows",  "5,287",    "80% split"),
    ("Test rows",      "1,322",    "20% split"),
    ("R2 Score",       "0.741",    "explains 74% of variance"),
    ("RMSE",           "607K ILS", "~35% of mean price"),
    ("Trees",          "500",      "depth 6, lr 0.05"),
])

pdf.info_box("XGBoost Hyperparameters", [
    "n_estimators = 500     |  Number of boosting trees",
    "learning_rate = 0.05   |  Step size - slow but stable convergence",
    "max_depth = 6          |  Tree depth - balances fit and overfitting",
    "subsample = 0.8        |  80% of rows sampled per tree",
    "colsample_bytree = 0.8 |  80% of features sampled per tree",
    "n_jobs = -1            |  Uses all available CPU cores",
])

pdf.section_title("8", "Key Features Used by the Model")
pdf.table(
    ["Feature", "Type", "Description"],
    [
        ["assetArea",           "Numeric",      "Apartment area in m2"],
        ["assetRoomNum",        "Numeric",      "Number of rooms"],
        ["floor_num",           "Numeric",      "Floor number (Hebrew names mapped to int)"],
        ["deal_year",           "Numeric",      "Year of transaction"],
        ["deal_month",          "Numeric",      "Month of transaction"],
        ["settlement_encoded",  "Category code","Settlement / city (label encoded)"],
        ["neighborhood_encoded","Category code","Neighborhood within city (label encoded)"],
        ["deal_nature_encoded", "Category code","Deal type (apartment type)"],
        ["street_price_mean",   "Target encoded","Mean sale price on this street"],
        ["socio_index_avg",     "Numeric",      "CBS socioeconomic index of the settlement"],
        ["socio_rank_avg",      "Numeric",      "CBS socioeconomic rank of the settlement"],
        ["X, Y",                "Numeric",      "ITM spatial coordinates"],
    ],
    [50, 36, 94]
)

# ?? PAGE 6: APP ???????????????????????????????????????????????????????????????
pdf.add_page()
pdf.section_title("9", "Web Application - app.py")
pdf.body_text(
    "The Streamlit app provides an interactive investment dashboard with two tabs. "
    "It loads the trained model at startup and computes settlement-level statistics "
    "by running predictions across all apartments in the dataset."
)

pdf.info_box("How the App Works (Mode A - Area Recommendations)", [
    "1. Load model.pkl and run predictions on apartments_ml_ready.csv",
    "2. Calculate gap_pct = (predicted - actual) / actual x 100 per apartment",
    "3. Compute annual price trend per settlement using linear regression on deal_year",
    "4. Aggregate: avg price, avg gap, deal count, avg socio index per settlement",
    "5. Filter by: max budget, risk level (socio above/below median), min deal count",
    "6. Score each settlement 0-100 using weighted combination of gap, trend, liquidity",
    "7. Display top 15 settlements ranked by viability score",
])

pdf.section_title("10", "User Profile Inputs")
pdf.table(
    ["Input", "Options", "Effect on Results"],
    [
        ["Max Budget (ILS)",    "300K - 10M (step 100K)",       "Filters out settlements above avg price"],
        ["Investment Goal",     "Current Yield / Appreciation", "Changes score weights (gap vs trend)"],
        ["Risk Level",          "Established / Emerging",       "Filters by socio index above/below median"],
        ["Min Deals (liquidity)","5 - 50",                      "Minimum transaction count threshold"],
    ],
    [40, 60, 80]
)

pdf.section_title("11", "Score Weights by Investment Goal")
pdf.table(
    ["Component", "Current Yield Weight", "Appreciation Weight"],
    [
        ["Price Gap (predicted vs actual)",  "60%", "30%"],
        ["Price Trend (% change per year)",  "20%", "50%"],
        ["Liquidity (deal count)",           "20%", "20%"],
    ],
    [90, 45, 45]
)

# ?? PAGE 7: FILES + STATUS ????????????????????????????????????????????????????
pdf.add_page()
pdf.section_title("12", "Complete File Structure")
pdf.table(
    ["File / Folder", "Role"],
    [
        ["app.py",                              "Streamlit web app - main entry point"],
        ["train_model.py",                      "Trains XGBoost model, saves model.pkl"],
        ["model.pkl",                           "Serialized trained model (~1.7 MB)"],
        ["requirements.txt",                    "Python dependencies"],
        ["run_app.bat",                         "Windows shortcut to launch the app"],
        ["DATA_FILES/ALL_DATA (1).xlsx",        "Raw source from Israel Tax Authority"],
        ["DATA_FILES/nadlan_loader.py",         "GovMap API scraper - data collection"],
        ["DATA_FILES/clean_data.py",            "Removes outliers from raw Excel"],
        ["DATA_FILES/prepare_ml_data.py",       "Full feature engineering pipeline"],
        ["DATA_FILES/nadlan_final.csv",         "10,424 cleaned transactions"],
        ["DATA_FILES/all_data_clean.csv",       "Price + area filtered dataset"],
        ["DATA_FILES/apartments_ml_ready.csv",  "Apartment features ready for XGBoost"],
        ["DATA_FILES/apartments_display.csv",   "UI-facing columns for the app"],
        ["DATA_FILES/ISRAEL_POINTS_FILTERED_GEO.csv", "Geographic reference / POI data"],
        ["DATA_FILES/BATYAM_2M/",               "Bat Yam single-city prototype scripts"],
        ["LAMAS_EDA_2M/PART1/",                "CBS socioeconomic EDA + dashboards"],
        ["LAMAS_EDA_2M/PART2/",                "Missing values + duplicate handling"],
        ["LAMAS_EDA_2M/PART3/",                "Final cleaned socioeconomic dataset"],
    ],
    [90, 90]
)

pdf.section_title("13", "Project Status")
pdf.table(
    ["Feature", "Status", "Notes"],
    [
        ["Data collection (GovMap scraper)",     "Done",        "10K deals across 20 regions"],
        ["Data cleaning pipeline",               "Done",        "Price, area, type filters"],
        ["Feature engineering",                  "Done",        "12+ ML-ready features"],
        ["Socioeconomic enrichment (LAMAS)",     "Done",        "Merged into every transaction"],
        ["XGBoost model training",               "Done",        "R2=0.741, RMSE=607K ILS"],
        ["Mode A - Area Recommendations",        "Live",        "Fully working in Streamlit"],
        ["Mode B - Property ranking in region",  "Planned",     "Not yet implemented"],
        ["Mode C - Single deal evaluation",      "Planned",     "Not yet implemented"],
        ["Mode D - Side-by-side comparison",     "Planned",     "Not yet implemented"],
        ["GIS map visualization",                "Planned",     "Folium/Leaflet mentioned"],
    ],
    [80, 22, 78]
)

pdf.ln(4)
pdf.set_font("Helvetica", "I", 9)
pdf.set_text_color(*GREY_TEXT)
pdf.cell(0, 6, "Generated automatically with Claude Code  |  May 2026", align="C")

pdf.output(OUTPUT)
print(f"PDF saved: {OUTPUT}")
