import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import chisquare
from scipy.stats import ks_2samp
from shapely.geometry import Polygon
from descartes.patch import PolygonPatch
from random import sample

try:
    from StringIO import BytesIO
except ImportError:
    from io import BytesIO

try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote
    
import base64

def df_comp(df1, df2, id1=None, id2=None, verbose=0):
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

	cstats['pct_mode_df1'] = cstats['variable'].apply(lambda x: np.mean(df1[x] == df1[x].value_counts().index[0]))
	cstats['pct_mode_df2'] = cstats['variable'].apply(lambda x: np.mean(df2[x] == df2[x].value_counts().index[0]))

	cstats['chisq_pval'] = cstats['variable'].apply(lambda x: chisq(df1[x],df2[x]))


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


	#cplots = {k: cat_comp_plot(df1[k], df2[k]) for k in t.loc[((t['diff']==False) & (t['df1_type']=='object'))].index}
	nplots = {k: num_comp_plot(df1[k], df2[k], name=k+' Range') for k in cols.loc[((cols['diff']==False) & (cols['df1_type']!='object'))].index}
	nplots_bytes = {k: image_to_Bytes(nplots[k][2]) for k in nplots.keys()}


	# optionaly print results
	if verbose>0:
		print "-------------------------------------------------------------------"
		print 
		print "VARIABLE OVERLAP COMPARISON"
		print
		print cols
		print
		if ((id1!=None) or (id2!=None)):
			if ((id1!=None) and (id2!=None)):
				print "-------------------------------------------------------------------"
				print 
				print "OPTIONAL ID VARIABLE COMPARISON"
				print
				print "id1 Unique  : ", ids['id1_uniq']
				print "id2 Unique  : ", ids['id2_uniq']
				print "id1 Only    : ", ids['id1_only']
				print "id2 Only    : ", ids['id2_only']
				print "Both        : ", ids['both']
				print
			else:
				print "-------------------------------------------------------------------"
				print 
				print "WARNING - only one ID variale ... comparison not run "
				print
		print "-------------------------------------------------------------------"
		print 
		print "CATEGORICAL VARIABLE COMPARISON STATS (top 25 vars)"
		print
		if len(cstats)<25:
			c_rows_print=len(cstats)
		else:
			c_rows_print=25
		print cstats[['variable','chisq_pval']].sort_values('chisq_pval').reset_index(drop=True)[0:c_rows_print]
		print "-------------------------------------------------------------------"
		print 
		print "NUMERICAL VARIABLE COMPARISON STATS (top 25 vars)"
		print
		if len(nstats)<25:
			n_rows_print=len(nstats)
		else:
			n_rows_print=25
		print nstats[['variable','ks_pval']].sort_values('ks_pval').reset_index(drop=True)[0:n_rows_print]

	return {'columns': cols,  
			'char_stats': cstats, 
			'num_stats': nstats, 
			'nplots': nplots,
			'nplots_bytes': nplots_bytes}


#  add a print function for variable distribution comps ... one for num and on for cat

def num_comp_plot(n1, n2, sampsize=1000, norm=True, name="Variable"):
    """Create ecdf plot comparing two numeric series distributions
    """
    s1 = np.array(sample(n1,min(len(n1),sampsize)))
    s2 = np.array(sample(n2,min(len(n2),sampsize)))

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

    fig = plt.figure(figsize=(9,6))
    ax = fig.add_subplot(111)
    patch = PolygonPatch(polygon, facecolor='lightgray', edgecolor='lightgray', alpha=0.5, zorder=2)
    ax.add_patch(patch)
    plt.plot(np.sort(s1), np.linspace(0, 1, len(s1), endpoint=False))
    plt.plot(np.sort(s2), np.linspace(0, 1, len(s2), endpoint=False))
    plt.ylabel("Empirical Cumulative Density")
    plt.xlabel(name)

    return name, polygon.area, fig



def cat_comp_plot(c1,c2):
	"""Create bar chart comparing two categorical series distributions
	"""
	vc1 = c1.value_counts(normalize=True,dropna=False)
	vc2 = c2.value_counts(normalize=True,dropna=False)
	df = pd.concat([vc1,vc2],axis=1).reset_index()
	df.columns = ['value','c1','c2']
	df['value'].fillna('NAN',inplace=True)
	df['c1'].fillna(0,inplace=True)
	df['c1'].fillna(0,inplace=True)
	df['sort'] = df['c1'] + df['c2']
	df.sort_values('sort',inplace=True)
	df.reset_index(inplace=True,drop=True)
	fig = plt.figure()
	ax = fig.add_subplot(111)
	ax.barh(df.index,df['c1'],.3,color='b',align='center')
	ax.barh(df.index+.3,df['c2'],.3,color='r',align='center')
	ax.set_yticks(df.index)
	ax.set_yticklabels(df['value'], rotation=40, ha='right')
	return fig


def chisq(base,compare):
	"""Runs a Chisquare test for two series of values
	"""

	if set(base.unique()) != set(compare.unique()):
		#print "Series DO NOT Have Same Value Sets"
		return "NA - diff values"

	elif base.nunique()==1:
		return "NA - only 1 value"

	else:
		expected = base.value_counts(normalize=True).sort_index() * len(compare)
		actual   = compare.value_counts().sort_index()

		if min(expected.append(actual)) <= 5:
			return "NA - small bin sizes"

		else:
			ch = chisquare(f_obs=actual,f_exp=expected)
			return ch[1]

    
def image_to_Bytes(img):        
    imgdata = BytesIO()
    img.savefig(imgdata)
    imgdata.seek(0)
    result_string = 'data:image/png;base64,' + \
        quote(base64.b64encode(imgdata.getvalue()))
    return result_string