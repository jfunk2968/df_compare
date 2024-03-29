import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import chisquare
from scipy.stats import ks_2samp
from shapely.geometry import Polygon
from descartes.patch import PolygonPatch

try:
    from StringIO import BytesIO
except ImportError:
    from io import BytesIO

try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote
    
import base64


def df_comp(df1, df2, id1=None, id2=None, max_cats=20, verbose=0, df1_name="DF-1", df2_name="DF-2"):
	"""Compares 2 pandas dataframes for differences
	"""

	# Compare variable sets
	#a = set(df1.columns)
	#b = set(df2.columns)
	#cols = {}
	#cols['a_only'] = a.difference(b)
	#cols['b_only'] = b.difference(a)
	#cols['both'] = a.intersection(b)

	# Compare data types for overlapping attributes
	cols = pd.concat([df1.dtypes,df2.dtypes],axis=1)
	cols.columns = ['df1_type','df2_type']

	cols['diff'] = cols.apply(lambda row: str(row['df1_type']) != str(row['df2_type']), axis=1)

	def same(row):
	    if str(row['df1_type']) == 'nan':
	        return 'df2_only'
	    elif str(row['df2_type']) == 'nan':
	        return 'df1_only'
	    else:
	        return 'both'

	cols['coverage'] = cols.apply(lambda row: same(row), axis=1)

	# Optionaly compare id variables
	ids = {}
	if ((id1!=None) and (id2!=None)):
		s_id1 = set(df1[id1])
		s_id2 = set(df2[id2])
		ids['id1_uniq'] = len(s_id1)==len(df1[id1])
		ids['id2_uniq'] = len(s_id2)==len(df2[id2])
		ids['id1_only'] = len(s_id1.difference(s_id1))
		ids['id2_only'] = len(s_id2.difference(s_id2))
		ids['both'] = len(s_id1.intersection(s_id2))
	else:
		ids['status'] = 'id comp not executed'


	# Build summary metric df for Categorical variables
	c_vars = cols.loc[((cols['diff']==False) & (cols['df1_type']=='object'))]	

	cstats = pd.DataFrame(list(c_vars.index),columns=['variable'])

	cstats['missing_df1'] = cstats['variable'].apply(lambda x: np.mean(df1[x].isnull()))
	cstats['missing_df2'] = cstats['variable'].apply(lambda x: np.mean(df2[x].isnull()))

	cstats['nunique_df1'] = cstats['variable'].apply(lambda x: df1[x].nunique())
	cstats['nunique_df2'] = cstats['variable'].apply(lambda x: df2[x].nunique())

	cstats['pct_mode_df1'] = cstats['variable'].apply(lambda x: np.mean(df1[x] == df1[x].value_counts().index[0]))
	cstats['pct_mode_df2'] = cstats['variable'].apply(lambda x: np.mean(df2[x] == df2[x].value_counts().index[0]))

	#cstats['chisq_pval'], cstats['chisq_outcome'] = zip(*cstats['variable'].apply(lambda x: chisq(df1[x],df2[x])))

	cplots = {k: cat_comp_plot(df1[k], df2[k], name=k+' Value', n1_name=df1_name, n2_name=df2_name) for k in 
		cstats['variable'].loc[((cstats['nunique_df1'] <  max_cats) &
								(cstats['nunique_df2'] <  max_cats))]}
	cplots_bytes = {k: image_to_Bytes(cplots[k][2]) for k in cplots.keys()}

	cstats['relative_diff'] = cstats['variable'].apply(lambda x: cplots.get(x, (0, -99, 0))[1])


	# Build summary metric df for Numerical variables	
	n_vars = cols.loc[((cols['diff']==False) & (cols['df1_type']!='object'))]	
	nstats = pd.DataFrame(list(n_vars.index),columns=['variable'])

	nstats['missing_df1'] = nstats['variable'].apply(lambda x: np.mean(df1[x].isnull()))
	nstats['missing_df2'] = nstats['variable'].apply(lambda x: np.mean(df2[x].isnull()))

	nstats['zero_df1'] = nstats['variable'].apply(lambda x: np.mean(df1[x] == 0))
	nstats['zero_df2'] = nstats['variable'].apply(lambda x: np.mean(df2[x] == 0))

	nstats['mean_df1'] = nstats['variable'].apply(lambda x: np.mean(df1[x]))
	nstats['mean_df2'] = nstats['variable'].apply(lambda x: np.mean(df2[x]))

	nstats['min_df1'] = nstats['variable'].apply(lambda x: min(df1[x]))
	nstats['min_df2'] = nstats['variable'].apply(lambda x: min(df2[x]))

	nstats['max_df1'] = nstats['variable'].apply(lambda x: max(df1[x]))
	nstats['max_df2'] = nstats['variable'].apply(lambda x: max(df2[x]))

	nstats['ks_pval'] = nstats['variable'].apply(lambda x: ks_2samp(df1[x],df2[x])[1])

	nplots = {k: num_comp_plot(df1[k], df2[k], norm=False, name=k, n1_name=df1_name, n2_name=df2_name) for k in cols.loc[((cols['diff']==False) & (cols['df1_type']!='object'))].index}
	nplots_bytes = {k: image_to_Bytes(nplots[k][2]) for k in nplots.keys()}

	nstats['relative_diff'] = nstats['variable'].apply(lambda x: nplots.get(x, (0, -99, 0))[1])


	# optionaly print results
	if verbose>0:
		print("-------------------------------------------------------------------")
		print()
		print("VARIABLE OVERLAP COMPARISON")
		print()
		print(cols)
		print()
		if ((id1!=None) or (id2!=None)):
			if ((id1!=None) and (id2!=None)):
				print("-------------------------------------------------------------------")
				print()
				print("OPTIONAL ID VARIABLE COMPARISON")
				print()
				print("id1 Unique  : ", ids['id1_uniq'])
				print("id2 Unique  : ", ids['id2_uniq'])
				print("id1 Only    : ", ids['id1_only'])
				print("id2 Only    : ", ids['id2_only'])
				print("Both        : ", ids['both'])
				print()
			else:
				print("-------------------------------------------------------------------")
				print() 
				print("WARNING - only one ID variale ... comparison not run ")
				print()
		print("-------------------------------------------------------------------")
		print() 
		print("CATEGORICAL VARIABLE COMPARISON STATS (top 25 vars)")
		print()
		if len(cstats)<25:
			c_rows_print=len(cstats)
		else:
			c_rows_print=25
		#print(cstats[['variable','chisq_pval', 'chisq_outcome']].sort_values('chisq_pval').reset_index(drop=True)[0:c_rows_print])
		print("-------------------------------------------------------------------")
		print() 
		print("NUMERICAL VARIABLE COMPARISON STATS (top 25 vars)")
		print()
		if len(nstats)<25:
			n_rows_print=len(nstats)
		else:
			n_rows_print=25
		print(nstats[['variable','ks_pval']].sort_values('ks_pval').reset_index(drop=True)[0:n_rows_print])

	return {'columns': cols,  
			'char_stats': cstats,
			'cplots': cplots,
			'cplots_bytes': cplots_bytes,
			'num_stats': nstats, 
			'nplots': nplots,
			'nplots_bytes': nplots_bytes}


#  add a print function for variable distribution comps ... one for num and on for cat


def num_comp_plot(n1, n2, sampsize=1000, norm=True, name="Variable", n1_name="DF-1", n2_name="DF-2"):
    """Create ecdf plot comparing two numeric series distributions
    """
    s1 = np.array(n1.sample(min(len(n1),sampsize)))
    s2 = np.array(n2.sample(min(len(n2),sampsize)))

    lower = float(min(min(n1),min(n2)))
    upper = float(max(max(n1),max(n2)))
    
    if norm==True:
        s1 = (s1-lower)/(upper-lower)
        s2 = (s2-lower)/(upper-lower)

    a = list(zip(np.sort(s1), np.linspace(0, 1, len(s1), endpoint=False)))
    b = list(zip(np.sort(s2), np.linspace(0, 1, len(s2), endpoint=False)))

    b.reverse()
    a.extend(b)
    a.append(a[0])
    polygon = Polygon(a)

    fig = plt.figure(figsize=(15,10))
    ax = fig.add_subplot(111)
    patch = PolygonPatch(polygon, facecolor='gray', edgecolor='lightgray', alpha=0.5, zorder=2)
    ax.add_patch(patch)
    plt.plot(np.sort(s1), np.linspace(0, 1, len(s1), endpoint=False), label=n1_name, color='red', linewidth=3)
    plt.plot(np.sort(s2), np.linspace(0, 1, len(s2), endpoint=False), label=n2_name, color='blue', linewidth=3)
    plt.title("Empirical Cumulative Density Comparison", fontsize=24, fontweight='bold')
    plt.ylabel("Cumulative Density", fontsize=20)
    plt.xlabel(name, fontsize=20)
    plt.tick_params(axis='both', which='major', labelsize=16)
    plt.legend(loc=0, fontsize=20)

    return name, polygon.area, fig


def cat_comp_plot(c1, c2, sampsize=1000, max_plot_values=20, name="Variable", n1_name="DF-1", n2_name="DF-2"):
    """Create bar chart comparing two categorical series distributions
    """
    footnote=""

    vc1 = c1.value_counts(normalize=True, dropna=False)
    vc2 = c2.value_counts(normalize=True, dropna=False)
    df = pd.concat([vc1,vc2], axis=1).reset_index()
    df.columns = ['value', 'c1', 'c2']
    df['value'].fillna('NAN', inplace=True)
    df['c1'].fillna(0, inplace=True)
    df['c2'].fillna(0, inplace=True)
    df['diff'] = abs(df['c1'] - df['c2'])
    df['sort'] = df['c1'] + df['c2']
    df.sort_values('sort', inplace=True)
    df.reset_index(inplace=True, drop=True)

    rel_diff = sum(df['diff'])/2.0

    if len(df)>max_plot_values:
    	footnote="* For clarity only the top "str(max_plot_values)+" most common values (of the "+str(len(df))+" unique values that exist in the data) are shown here"
    	df = df[0:max_plot_values-1]

    fig = plt.figure(figsize=(15,10))
    ax = fig.add_subplot(111)
    ax.barh(df.index-.15, df['c1'], .3, color='b', edgecolor='gray', align='center', label=n1_name)
    ax.barh(df.index+.15, df['c2'], .3, color='r', edgecolor='gray', align='center', label=n2_name)
    ax.set_yticks(df.index)
    ax.set_yticklabels(df['value'], ha='right')
    
    plt.ylabel(name+" Value", fontsize=20)
    plt.xlabel("Percent", fontsize=20)
    plt.title("Empirical Distribution Comparison", fontsize=24, fontweight='bold')
    plt.tick_params(axis='both', which='major', labelsize=16)
    plt.legend(loc=0, fontsize=20)

    plt.figtext(0.1, 0.01, footnote, horizontalalignment='left', fontsize=14)

    return df, rel_diff, fig


def chisq(base,compare):
	"""Runs a Chisquare test for two series of values
	"""

	if set(base.unique()) != set(compare.unique()):
		#print "Series DO NOT Have Same Value Sets"
		return (0, "NA - diff values")

	elif base.nunique()==1:
		return (0, "NA - only 1 value")

	else:
		expected = base.value_counts(normalize=True).sort_index() * len(compare)
		actual   = compare.value_counts().sort_index()

		if min(expected.append(actual)) <= 5:
			return (0, "NA - small bin sizes")

		else:
			ch = chisquare(f_obs=actual,f_exp=expected)
			return (ch[1], "Valid Score")

    
def image_to_Bytes(img):        
    imgdata = BytesIO()
    img.savefig(imgdata)
    imgdata.seek(0)
    result_string = 'data:image/png;base64,' + \
        quote(base64.b64encode(imgdata.getvalue()))
    return result_string