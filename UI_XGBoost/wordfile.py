
def func(k):
    words_list = {
        "ocean" : "collateral", 
        "le" : "legal entity",
        "air":"assumed interest rate",
		"apr":"annual percentage rate",
		"arm":"adjustable rate mortgage",
        "arpu": "average revenue per user",
        "b2b": "business to business",
        "b2c": "business to consumer",
        "capex" : "capital expenditures",

		"cd":"certificate of deposit",
		"cds" : "credit default swap",
		"ceo" : "chief executive officer",


		"cfc" : "consumption of fixed capital",


		"cfct" : "cash flow cycle time",


		"cfo" : "chief financial officer",


		"cima" : "certified institutes of management accounting",


		"cmo" : "chief marketing officer",


		"cob" : "close of business",


		"cogs" : "cost of goods sold",


		"coo" : "chief operating officer",


		"crm" : "customer relationship management",


		"cto" : "chief technology officer",


		"ebit" : "earnings before interest and taxes",

		"ebitda" : "earnings before interest, taxes, depreciation, and amortization",


		"edi" : "electronic data interchange",
		"eft":"electronic funds transfer",

		"eps" : "earnings per share",
		"etf":"exchange traded funds",

		"fifo" : "first in, first out",
		"fdic":"federal deposit insurance corporation",

		"fl" : "financial leverage",
		"forex":"foreign exchange",
		"frb":"federal reserve board",


		"gaap" : "generally accepted accounting principles",


		"gfcf" : "gross fixed capital formation",


		"gp" : "gross profit",
		"gnp":"gross national product",


		"hr" : "human resources",


		"icb" : "industry classification benchmark",


		"icrm" : "innovative customer relationship management",


		"ie" : "interest expense",
		"ira":"individual retirement account",


		"ipo" : "initial public offering",


		"libor" : "london interbank offered rate",


		"lifo" : "last in, first out",
		"loi":"letter of intent",


		"llc" : "limited liability company",
		"mmkt":"money market",


		"nav" : "net asset value",


		"nda" : "non-disclosure agreement",


		"nopat" : "net operating profit after tax",
		"nav":"net asset value",
		"nyse":"new york stock exchange",

		"npv" : "net present value",


		"opex" : "operational expenditures",


		"po" : "profit objective",


		"po" : "purchase order",
		"psp":"profit sharing plan",


		"pp&e" : "property, plant, and equipment",


		"p&l" : "profit and loss",


		"r&d" : "research and development",


		"re" : "retained earnings",
		"reit":"real estate investment trust",


		"roa" : "return on assets",


		"roce" : "return on capital employed",


		"roe" : "return on equity",


		"roi" : "return on investment",


		"roic" : "return on invested capital",


		"rona" : "return on net assets",


		"ros" : "return on sales",


		"rr" : "resource rent",
		"sec":"securities exchange commission",


		"st" : "sales during time period t",


		"scm" : "supply chain management",


		"sg&a" : "sales, general, and administrative expenses",


		"soho" : "small office/home office",
		"tsa":"tax-sheltered annuity",


		"tco" : "total cost of ownership",


		"tsr" : "total shareholder return",


		"wacc" : "weighted average cost of capital",


		"wc" : "working capital",
		"ytm":"yield to maturity",


		"pmac" : "period moving average cost",


		"p/e" : "price per earning", 

    }

    if k in words_list.keys():
        return words_list[k]
    else :
        return None

# c = func("hi")
# print(c)
