#!/usr/bin/env python3
import string
import os
import json
import time
import glob
import shutil
import png

base_dir = os.path.dirname(__file__)

class DataPoint(object):
	def __init__(self, date, case_total, death_total):
		self.date = date
		self.case_total = case_total
		self.death_total = death_total
		self.case_increase = None
		self.death_increase = None
		self.case_increase_average = None
		self.death_increase_average = None

	def __repr__(self):
		return f"{self.date}: {self.case_total} ({self.case_increase}), {self.death_total} ({self.death_increase})"

class DataSet(object):
	def __init__(self, data, late_start = False):
		self.data = data
		if len(self.data) == 0:
			self.case_total = 0
			self.cases_today = 0
			self.cases_this_week = 0
			self.death_total = 0
			self.deaths_today = 0
			self.deaths_this_week = 0
			return

		if late_start:
			self.data[0].case_increase = None
			self.data[0].death_increase = None
		else:
			self.data[0].case_increase = self.data[0].case_total
			self.data[0].death_increase = self.data[0].death_total
		for i in range(1, len(self.data)):
			self.data[i].case_increase = self.data[i].case_total - self.data[i - 1].case_total
			self.data[i].death_increase = self.data[i].death_total - self.data[i - 1].death_total

		if late_start:
			avg_begin = 7
		else:
			avg_begin = 0
		for i in range(avg_begin, len(self.data)):
			if i >= 7:
				prev_cases = self.data[i - 7].case_total
				prev_deaths = self.data[i - 7].death_total
			else:
				prev_cases = 0
				prev_deaths = 0
			self.data[i].case_increase_average = (self.data[i].case_total - prev_cases) / 7.0
			self.data[i].death_increase_average = (self.data[i].death_total - prev_deaths) / 7.0

		for i in range(0, len(self.data)):
			if self.data[i].case_increase is not None and self.data[i].case_increase < 0:
				self.data[i].case_increase = 0
			if self.data[i].case_increase_average is not None and self.data[i].case_increase_average < 0:
				self.data[i].case_increase_average = 0
			if self.data[i].death_increase is not None and self.data[i].death_increase < 0:
				self.data[i].death_increase = 0
			if self.data[i].death_increase_average is not None and self.data[i].death_increase_average < 0:
				self.data[i].death_increase_average = 0

		self.case_total = self.data[-1].case_total
		self.death_total = self.data[-1].death_total
		self.cases_today = self.data[-1].case_increase
		self.deaths_today = self.data[-1].death_increase
		if self.cases_today is None:
			self.cases_today = 0
		if self.deaths_today is None:
			self.deaths_today = 0
		if len(self.data) > 7:
			self.cases_this_week = self.data[-1].case_total - self.data[-8].case_total
			self.deaths_this_week = self.data[-1].death_total - self.data[-8].death_total
		else:
			self.cases_this_week = self.data[-1].case_total - self.data[0].case_total
			self.deaths_this_week = self.data[-1].death_total - self.data[0].death_total
		if len(self.data) > 14:
			self.cases_last_two_weeks = self.data[-1].case_total - self.data[-15].case_total
			self.deaths_last_two_weeks = self.data[-1].death_total - self.data[-15].death_total
		else:
			self.cases_last_two_weeks = self.data[-1].case_total - self.data[0].case_total
			self.deaths_last_two_weeks = self.data[-1].death_total - self.data[0].death_total
		if self.cases_this_week < 0:
			self.cases_this_week = 0
		if self.cases_last_two_weeks < 0:
			self.cases_last_two_weeks = 0
		if self.deaths_this_week < 0:
			self.deaths_this_week = 0
		if self.deaths_last_two_weeks < 0:
			self.deaths_last_two_weeks = 0

	def __repr__(self):
		return repr(self.data)

	def generate_case_graph(self, name, height):
		template = string.Template(open(os.path.join(base_dir, 'src/graph.template.html'), 'r').read())
		replacements = {"name": name, "label": "Cases", "height": str(height),
			"color": "128, 198, 233"}
		dates = []
		values = []
		averages = []
		for pt in self.data:
			if pt.date < "2020-03-15":
				continue
			if pt.case_increase is None:
				continue
			dates.append(pt.date)
			values.append(str(pt.case_increase))
			if pt.case_increase_average is None:
				averages.append("undefined")
			else:
				averages.append(f"{pt.case_increase_average:.1f}")
		replacements["dates"] = ','.join([f'"{i}"' for i in dates])
		replacements["values"] = ','.join(values)
		replacements["averages"] = ','.join(averages)
		return template.substitute(replacements)

	def generate_death_graph(self, name, height):
		template = string.Template(open(os.path.join(base_dir, 'src/graph.template.html'), 'r').read())
		replacements = {"name": name, "label": "Deaths", "height": str(height),
			"color": "222, 143, 151"}
		dates = []
		values = []
		averages = []
		for pt in self.data:
			if pt.date < "2020-03-15":
				continue
			if pt.death_increase is None:
				continue
			dates.append(pt.date)
			values.append(str(pt.death_increase))
			if pt.death_increase_average is None:
				averages.append("undefined")
			else:
				averages.append(f"{pt.death_increase_average:.1f}")
		replacements["dates"] = ','.join([f'"{i}"' for i in dates])
		replacements["values"] = ','.join(values)
		replacements["averages"] = ','.join(averages)
		return template.substitute(replacements)

	def case_count_description(self):
		total = self.case_total
		if total == 1:
			total_label = "case"
		else:
			total_label = "cases"
		if len(self.data) == 1:
			return f"{total} {total_label} total"
		day = self.cases_today
		if day == 1:
			day_label = "case"
		else:
			day_label = "cases"
		if (total - day) == 0:
			day_percent = "no previous"
		else:
			day_percent = f"+{(day * 100.0) / (total - day):.2f}%"
		week = self.cases_this_week
		if week == 1:
			week_label = "case"
		else:
			week_label = "cases"
		if (total - week) == 0:
			week_percent = "no previous"
		else:
			week_percent = f"+{(week * 100.0) / (total - week):.2f}%"
		return f"{total} {total_label} total, {day} {day_label} today ({day_percent}), {week} {week_label} this week ({week_percent})"

	def death_count_description(self):
		total = self.death_total
		if total == 1:
			total_label = "death"
		else:
			total_label = "deaths"
		day = self.deaths_today
		if day == 1:
			day_label = "death"
		else:
			day_label = "deaths"
		week = self.deaths_this_week
		if week == 1:
			week_label = "death"
		else:
			week_label = "deaths"
		if (total - day) == 0:
			day_percent = "no previous"
		else:
			day_percent = f"+{(day * 100.0) / (total - day):.2f}%"
		if (total - week) == 0:
			week_percent = "no previous"
		else:
			week_percent = f"+{(week * 100.0) / (total - week):.2f}%"
		return f"{total} {total_label} total, {day} {day_label} today ({day_percent}), {week} {week_label} this week ({week_percent})"

def generate_page(title, src, out, replacements):
	replacements["title"] = title
	template = string.Template(open(os.path.join(base_dir, "src", src)).read())
	out = os.path.join(base_dir, "out", out)
	open(out, 'w').write(template.substitute(replacements))

def import_us_total_case_data():
	raw_data = open(os.path.join(base_dir, 'data/us.csv'), 'r').read().split('\n')[1:]
	out = []
	for line in raw_data:
		date, cases, deaths = line.split(',')
		out.append(DataPoint(date, int(cases), int(deaths)))
	return DataSet(out)

def import_us_state_data():
	raw_data = open(os.path.join(base_dir, 'data/us-states.csv'), 'r').read().split('\n')[1:]
	state_mapping = {}
	state_cases = {}
	for line in raw_data:
		if len(line) == 0:
			continue
		date, state, fips, cases, deaths = line.split(',')
		if state not in state_mapping:
			state_mapping[state] = fips
		if state not in state_cases:
			state_cases[state] = []
		state_cases[state].append(DataPoint(date, int(cases), int(deaths)))
	for state in state_cases.keys():
		state_cases[state] = DataSet(state_cases[state])
	return state_mapping, state_cases

def import_us_county_data():
	raw_data = open(os.path.join(base_dir, 'data/us-counties.csv'), 'r').read().split('\n')[1:]
	county_mapping = {}
	county_to_fips = {}
	county_state = {}
	county_cases = {}
	for line in raw_data:
		if len(line) == 0:
			continue
		date, county, state, fips, cases, deaths = line.split(',')
		if county == "New York City":
			fips = "36NYC"
		if fips not in county_mapping:
			county_mapping[fips] = county
		if fips not in county_state:
			county_state[fips] = state
		if fips not in county_cases:
			county_cases[fips] = []
		if state not in county_to_fips:
			county_to_fips[state] = {}
		county_cases[fips].append(DataPoint(date, int(cases), int(deaths)))
		county_to_fips[state][county] = fips
	for fips in county_cases:
		county_cases[fips] = DataSet(county_cases[fips])
	return county_mapping, county_to_fips, county_state, county_cases

def import_latest_fl_county_totals():
	raw_data = json.loads(open(os.path.join(base_dir, 'data/fl-county-totals.json')).read())
	out = {}
	for entry in raw_data["features"]:
		out[f'12{entry["attributes"]["COUNTY"]}'] = DataPoint(
			time.strftime('%Y-%m-%d'), int(entry["attributes"]["CasesAll"]),
			int(entry["attributes"]["Deaths"]))
	return out

def import_fl_zip_case_data():
	dates = []
	for filename in glob.glob(os.path.join(base_dir, 'data/fl-zip-cases-*.json')):
		dates.append(filename[len(os.path.join(base_dir, 'data/fl-zip-cases-')):-len('.json')])
	dates.sort()

	out = {}
	for date in dates:
		raw_data = json.loads(open(os.path.join(base_dir, f'data/fl-zip-cases-{date}.json')).read())
		for entry in raw_data["features"]:
			zipcode = entry["attributes"]["ZIP"]
			county = entry["attributes"]["COUNTYNAME"]
			if county == "Dade":
				county = "Miami-Dade"
			if county == "Desoto":
				county = "DeSoto"
			if county not in out:
				out[county] = {}
			if zipcode not in out[county]:
				out[county][zipcode] = []
			cases = 0
			try:
				cases = int(entry["attributes"]["Cases_1"])
			except:
				pass
			out[county][zipcode].append(DataPoint(date, cases, 0))

	for county in out.keys():
		for zipcode in out[county].keys():
			out[county][zipcode] = DataSet(out[county][zipcode], True)
	return out

def import_fl_zip_info():
	raw_data = json.loads(open(os.path.join(base_dir, 'data/fl-zip-info.json')).read())
	zip_county = {}
	zip_by_county = {}
	zip_names = {}
	zip_polys = {}
	for entry in raw_data["features"]:
		county = entry["attributes"]["COUNTYNAME"]
		if county == "Dade":
			county = "Miami-Dade"
		if county == "Desoto":
			county = "DeSoto"
		if county not in zip_by_county:
			zip_by_county[county] = []
		if county not in zip_polys:
			zip_polys[county] = {}
		zip_county[entry["attributes"]["ZIP"]] = county
		zip_by_county[county].append(entry["attributes"]["ZIP"])
		zip_names[entry["attributes"]["ZIP"]] = entry["attributes"]["Places"]
		zip_polys[county][entry["attributes"]["ZIP"]] = entry["geometry"]["rings"]
	return zip_county, zip_by_county, zip_names, zip_polys

def import_state_info():
	raw_data = json.loads(open(os.path.join(base_dir, 'data/us-state-info.json')).read())
	state_polys = {}
	for entry in raw_data["features"]:
		state = entry["properties"]["NAME"]
		if entry["geometry"]["type"] == "Polygon":
			state_polys[state] = [entry["geometry"]["coordinates"][0]]
		else:
			state_polys[state] = []
			for poly in entry["geometry"]["coordinates"]:
				state_polys[state].append(poly[0])
		for poly in state_polys[state]:
			for pt in poly:
				pt[1] = pt[1] * 1.2
	return state_polys

def import_county_info():
	raw_data = json.loads(open(os.path.join(base_dir, 'data/us-county-info.json'), 'rb').read().decode('charmap'))
	county_polys = {}
	for entry in raw_data["features"]:
		county = entry["properties"]["STATE"] + entry["properties"]["COUNTY"]
		if entry["geometry"]["type"] == "Polygon":
			county_polys[county] = [entry["geometry"]["coordinates"][0]]
		else:
			county_polys[county] = []
			for poly in entry["geometry"]["coordinates"]:
				county_polys[county].append(poly[0])
		for poly in county_polys[county]:
			for pt in poly:
				pt[1] = pt[1] * 1.2
	return county_polys

def generate_case_breakdown(title, target, data_set, graph):
	if target is None:
		template = string.Template(open(os.path.join(base_dir, 'src/breakdown-nolink.template.html'), 'r').read())
	else:
		template = string.Template(open(os.path.join(base_dir, 'src/breakdown.template.html'), 'r').read())
	count = data_set.case_count_description()
	replacements = {"title": title, "target": target, "count": count, "graph": graph}
	return template.substitute(replacements)

def generate_tooltip(name, title, data_set, with_deaths):
	template = string.Template(open(os.path.join(base_dir, 'src/tooltip.template.html'), 'r').read())
	count = data_set.case_count_description()
	if with_deaths:
		count += '<br/><br/>' + data_set.death_count_description()
	replacements = {"name": name, "title": title, "count": count}
	return template.substitute(replacements)

def generate_svg(colors, links, tooltips, polys, size):
	name_list = list(colors.keys())

	width = size
	height = size

	min_x = polys[name_list[0]][0][0][0]
	min_y = polys[name_list[0]][0][0][1]
	max_x = min_x
	max_y = min_y
	for name in name_list:
		for poly in polys[name]:
			for pt in poly:
				if pt[0] < min_x:
					min_x = pt[0]
				if pt[0] > max_x:
					max_x = pt[0]
				if pt[1] < min_y:
					min_y = pt[1]
				if pt[1] > max_y:
					max_y = pt[1]
	if (max_x - min_x) > (max_y - min_y):
		height = (width * (max_y - min_y)) / (max_x - min_x)
	else:
		width = (height * (max_x - min_x)) / (max_y - min_y)
	x_offset = -min_x
	x_factor = width / (max_x - min_x)
	y_offset = -min_y
	y_factor = height / (max_y - min_y)

	out = f'<svg version="1.1" baseProfile="full" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'

	for name in name_list:
		for poly in polys[name]:
			out += '<polygon points="'
			for pt in poly:
				out += f'{(pt[0] + x_offset) * x_factor},{height - ((pt[1] + y_offset) * y_factor)} '
			out += f'" fill="{colors[name]}" stroke="#282828" stroke-width="2" '
			if name in tooltips:
				out += f'onmousemove="showTooltip(evt, \'{tooltips[name]}\');" '
				out += f'onmouseout="hideTooltip(\'{tooltips[name]}\');" '
			if name in links:
				out += f'onclick="document.location.href = \'{links[name]}\';" '
			out += '/>\n'

	out += '</svg>\n'
	return out

def interpolate_color(a, b, frac):
	r = (a[0] * (1 - frac)) + (b[0] * frac)
	g = (a[1] * (1 - frac)) + (b[1] * frac)
	b = (a[2] * (1 - frac)) + (b[2] * frac)
	return f'#{int(r):02x}{int(g):02x}{int(b):02x}'

def color_for_value(value, max_value):
	if value == 0:
		return "#484848"
	value_frac = value / max_value
	if value_frac <= 0.1:
		return interpolate_color((72, 72, 72), (128, 198, 233), value_frac / 0.1)
	elif value_frac <= 0.5:
		return interpolate_color((128, 198, 233), (237, 223, 179), (value_frac - 0.1) / 0.4)
	else:
		return interpolate_color((237, 223, 179), (222, 143, 151), (value_frac - 0.5) / 0.5)

def generate_heat_map_legend():
	pixels = []
	for y in range(8):
		row = ()
		for x in range(400):
			value = color_for_value(x, 399)
			r = int(value[1:3], 16)
			g = int(value[3:5], 16)
			b = int(value[5:7], 16)
			row += (r, g, b)
		pixels.append(row)
	out = open(os.path.join(base_dir, "out/heatmap.png"), 'wb')
	png.Writer(400, 8, greyscale=False).write(out, pixels)

total_cases = import_us_total_case_data()
state_mapping, state_cases = import_us_state_data()
county_mapping, county_to_fips, county_state, county_cases = import_us_county_data()
latest_fl_county_cases = import_latest_fl_county_totals()
fl_zip_cases = import_fl_zip_case_data()
fl_zip_county, fl_zip_by_county, fl_zip_names, fl_zip_polys = import_fl_zip_info()
state_polys = import_state_info()
county_polys = import_county_info()

state_counties = {}
for state in state_cases.keys():
	state_counties[state] = []
	fips = state_mapping[state]
	for county in county_mapping.keys():
		if county.startswith(fips):
			state_counties[state].append(county)

# Compute latest Florida totals from county data
latest_fl_case_total = 0
latest_fl_death_total = 0
for county in latest_fl_county_cases.values():
	latest_fl_case_total += county.case_total
	latest_fl_death_total += county.death_total

# Update Florida case information with latest data from FDoH (NY Times data is one day behind)
if latest_fl_case_total != state_cases["Florida"].case_total:
	state_cases["Florida"].data.append(DataPoint(time.strftime('%Y-%m-%d'),
		latest_fl_case_total, latest_fl_death_total))
	state_cases["Florida"] = DataSet(state_cases["Florida"].data)
	for county in latest_fl_county_cases.keys():
		if county in county_cases:
			county_cases[county].data.append(latest_fl_county_cases[county])
			county_cases[county] = DataSet(county_cases[county].data)

if os.path.exists(os.path.join(base_dir, "out")):
	shutil.rmtree(os.path.join(base_dir, "out"))
os.mkdir(os.path.join(base_dir, "out"))

shutil.copy(os.path.join(base_dir, "src/style.css"), os.path.join(base_dir, "out/style.css"))
shutil.copy(os.path.join(base_dir, "src/Chart.min.js"), os.path.join(base_dir, "out/Chart.min.js"))
shutil.copy(os.path.join(base_dir, "src/Chart.min.css"), os.path.join(base_dir, "out/Chart.min.css"))
shutil.copy(os.path.join(base_dir, "src/tooltip.js"), os.path.join(base_dir, "out/tooltip.js"))

state_ranking = list(state_cases.keys())
state_ranking.sort(key=lambda state: (state_cases[state].cases_this_week,
	state_cases[state].case_total), reverse=True)

replacements = {}
replacements["us_count"] = (total_cases.case_count_description() + "<br/>" +
	total_cases.death_count_description())
replacements["us_graph"] = (total_cases.generate_case_graph("total", 200) + "<br/>" +
	total_cases.generate_death_graph("total_deaths", 100))

replacements["us_graph"] += "<hr/>"
replacements["us_graph"] += '<div align="center"><h2>Cases this week by state</h2>'
colors = {}
links = {}
tooltips = {}
max_value = 0
state_list = ['Minnesota', 'Indiana', 'Alabama', 'Maryland', 'Washington', 'New Hampshire',
	'Mississippi', 'New York', 'Arizona', 'Delaware', 'Wyoming', 'Montana', 'North Carolina',
	'Florida', 'North Dakota', 'West Virginia', 'Oklahoma', 'Illinois', 'Vermont', 'Iowa',
	'Wisconsin', 'New Mexico', 'California', 'District of Columbia', 'Missouri', 'Virginia',
	'Louisiana', 'Utah', 'Michigan', 'Connecticut', 'Arkansas', 'Nevada', 'Idaho', 'Ohio',
	'Texas', 'South Dakota', 'Kansas', 'Rhode Island', 'Massachusetts', 'New Jersey',
	'Tennessee', 'Pennsylvania', 'Oregon', 'Kentucky', 'Colorado', 'Georgia', 'South Carolina',
	'Maine', 'Nebraska']
for state in state_list:
	value = state_cases[state].cases_this_week
	if value > max_value:
		max_value = value
for state in state_list:
	colors[state] = color_for_value(state_cases[state].cases_this_week, max_value)
	links[state] = f'{state.replace(" ", "_")}.html'
	tooltips[state] = f'state_tooltip_{state.replace(" ", "_")}'
replacements["us_graph"] += f'0 <img src="heatmap.png"></img> {max_value}'
replacements["us_graph"] += '<br/></br/>'
replacements["us_graph"] += generate_svg(colors, links, tooltips, state_polys, 1000)
replacements["us_graph"] += '</div>'

state_graph = ""
for state in state_ranking:
	state_graph += generate_case_breakdown(state, f"{state.replace(' ', '_')}.html", state_cases[state],
		state_cases[state].generate_case_graph(state.replace(' ', '_'), 150))
	state_graph += generate_tooltip(f"state_tooltip_{state.replace(' ', '_')}", state,
		state_cases[state], True)
replacements["state_graph"] = state_graph
generate_page("United States of America", "index.html", "index.html", replacements)

for state in state_ranking:
	county_ranking = state_counties[state]
	county_ranking.sort(key=lambda county: (county_cases[county].cases_this_week,
		county_cases[county].case_total), reverse=True)

	replacements = {}
	replacements["state_count"] = (state_cases[state].case_count_description() + "<br/>" +
		state_cases[state].death_count_description())
	replacements["state_graph"] = (state_cases[state].generate_case_graph("total", 200) + "<br/>" +
		state_cases[state].generate_death_graph("total_deaths", 100))

	if len(county_ranking) != 0:
		replacements["state_graph"] += "<hr/>"
		replacements["state_graph"] += '<div align="center"><h2>Cases this week by county</h2>'
		colors = {}
		links = {}
		tooltips = {}
		max_value = 0
		county_list = []
		for county in county_polys.keys():
			if county.startswith(state_mapping[state]):
				county_list.append(county)
		for county in county_list:
			if county in county_cases:
				value = county_cases[county].cases_this_week
				if value > max_value:
					max_value = value
		for county in county_list:
			if county in county_cases:
				cases = county_cases[county].cases_this_week
			else:
				cases = 0
			colors[county] = color_for_value(cases, max_value)
			links[county] = f'county-{county}.html'
			tooltips[county] = f'county_tooltip_{county}'
		replacements["state_graph"] += f'0 <img src="heatmap.png"></img> {max_value}'
		replacements["state_graph"] += '<br/></br/>'
		replacements["state_graph"] += generate_svg(colors, links, tooltips, county_polys, 800)
		replacements["state_graph"] += '</div>'

	county_graph = ""
	for county in county_ranking:
		county_graph += generate_case_breakdown(county_mapping[county], f"county-{county}.html", county_cases[county],
			county_cases[county].generate_case_graph(f"county_{county}", 150))
		county_graph += generate_tooltip(f"county_tooltip_{county}", county_mapping[county],
			county_cases[county], True)
	replacements["county_graph"] = county_graph
	generate_page(state, "state.html", f"{state.replace(' ', '_')}.html", replacements)

for county in county_cases.keys():
	replacements = {}
	replacements["county_count"] = (county_cases[county].case_count_description() + "<br/>" +
		county_cases[county].death_count_description())
	replacements["county_graph"] = (county_cases[county].generate_case_graph("total", 200) + "<br/>" +
		county_cases[county].generate_death_graph("total_deaths", 100))
	replacements["state"] = county_state[county]
	replacements["state_link"] = f"{county_state[county].replace(' ', '_')}.html"

	if county_state[county] == "Florida" and county_mapping[county] in fl_zip_by_county:
		zip_available = fl_zip_by_county[county_mapping[county]]
		zip_ranking = []
		for zipcode in zip_available:
			if len(fl_zip_cases[county_mapping[county]][zipcode].data) > 0:
				zip_ranking.append(zipcode)
		zip_ranking.sort(key=lambda zipcode: (fl_zip_cases[county_mapping[county]][zipcode].cases_this_week,
			fl_zip_cases[county_mapping[county]][zipcode].case_total), reverse=True)

		replacements["county_graph"] += "<hr/>"
		replacements["county_graph"] += '<div align="center"><h2>Cases this week by ZIP code</h2>'
		colors = {}
		links = {}
		tooltips = {}
		max_value = 0
		for zipcode in zip_ranking:
			value = fl_zip_cases[county_mapping[county]][zipcode].cases_this_week
			if value > max_value:
				max_value = value
		for zipcode in fl_zip_by_county[county_mapping[county]]:
			if zipcode in zip_ranking:
				colors[zipcode] = color_for_value(fl_zip_cases[county_mapping[county]][zipcode].cases_this_week, max_value)
				links[zipcode] = f'#zip{zipcode}'
				tooltips[zipcode] = f'zip_tooltip_{zipcode}'
			else:
				colors[zipcode] = color_for_value(0, max_value)
		replacements["county_graph"] += f'0 <img src="heatmap.png"></img> {max_value}'
		replacements["county_graph"] += '<br/></br/>'
		replacements["county_graph"] += generate_svg(colors, links, tooltips, fl_zip_polys[county_mapping[county]], 800)
		replacements["county_graph"] += '</div>'

		zip_graph = ""
		for zipcode in zip_ranking:
			zip_graph += f'<a name="zip{zipcode}"></a>'
			zip_graph += generate_case_breakdown(f"{zipcode} - {fl_zip_names[zipcode]}", None,
				fl_zip_cases[county_mapping[county]][zipcode],
				fl_zip_cases[county_mapping[county]][zipcode].generate_case_graph(f"zip_{zipcode}", 150))
			zip_graph += generate_tooltip(f"zip_tooltip_{zipcode}", f"{zipcode} - {fl_zip_names[zipcode]}",
				fl_zip_cases[county_mapping[county]][zipcode], False)
		replacements["zip_graph"] = zip_graph
		generate_page(county_mapping[county], "fl-county.html", f"county-{county}.html", replacements)
	else:
		generate_page(county_mapping[county], "county.html", f"county-{county}.html", replacements)

generate_heat_map_legend()
