import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import chisquare
from scipy.stats import ks_2samp


def df_comp(df1,df2,id1=None,id2=None):
	"""Compares 2 pandas dataframes for differences
	"""
	# Compare variable sets

	a = set(df1.columns)
	b = set(df2.columns)

	print "-------------------------------------------------------------------"
	print 
	print "VARIABLE OVERLAP COMPARISON"
	print
	print "# Columns in df1 only   :",len(a.difference(b))
	print 
	print pd.DataFrame(list(a.difference(b)),columns=['Variable']).sort_values('Variable').reset_index(drop=True)
	print 
	print "# Columns in df2 only   :",len(b.difference(a))
	print
	print pd.DataFrame(list(b.difference(a)),columns=['Variable']).sort_values('Variable').reset_index(drop=True)
	print 

	cols = a.intersection(b)

	print "# Columns in both       :",len(cols)
	print 
	print pd.DataFrame(list(cols),columns=['Variable']).sort_values('Variable').reset_index(drop=True)
	print


	# Compare data types for overlapping attributes

	print "-------------------------------------------------------------------"
	print 
	print "VARIABLE DATA TYPE COMPARISON (for common variables)"
	print

	t = pd.concat([df1.dtypes[cols],df2.dtypes[cols]],axis=1)
	t.columns = ['df1_type','df2_type']
	t['diff'] = t['df1_type'] != t['df2_type']

	print sum(t['diff'])," Common variables have different data types"
	print

	if sum(t['diff'])>0:
		print "Variables with different types:"
		print 
		print t[['df1_type','df2_type']].loc[t['diff']==True]
		print

	# Optionaly compare id variables

	if ((id1!=None) or (id2!=None)):
		if ((id1!=None) and (id2!=None)):
			print "-------------------------------------------------------------------"
			print 
			print "OPTIONAL ID VARIABLE COMPARISON"
			print
			compare(df1[id1],df2[id2])
			print
		else:
			print "-------------------------------------------------------------------"
			print 
			print "WARNING - only one ID variale ... comparison not run "
			print


	# Build summary metric df for Categorical variables

	c_vars = t.loc[((t['diff']==False) & (t['df1_type']=='object'))]	
	cstats = pd.DataFrame(list(c_vars.index),columns=['variable'])

	cstats['missing_df1'] = cstats['variable'].apply(lambda x: np.mean(df1[x].isnull()))
	cstats['missing_df2'] = cstats['variable'].apply(lambda x: np.mean(df2[x].isnull()))

	cstats['pct_mode_df1'] = cstats['variable'].apply(lambda x: np.mean(df1[x] == df1[x].value_counts().index[0]))
	cstats['pct_mode_df2'] = cstats['variable'].apply(lambda x: np.mean(df2[x] == df2[x].value_counts().index[0]))

	cstats['chisq_pval'] = cstats['variable'].apply(lambda x: chisq(df1[x],df2[x]))

	print "-------------------------------------------------------------------"
	print 
	print "CATEGORICAL VARIABLE COMPARISON STATS (top 25 vars)"
	print

	if len(cstats)<25:
		c_rows_print=len(cstats)
	else:
		c_rows_print=25

	print cstats[['variable','chisq_pval']].sort_values('chisq_pval').reset_index(drop=True)[0:c_rows_print]


	# Build summary metric df for Numerical variables	

	n_vars = t.loc[((t['diff']==False) & (t['df1_type']!='object'))]	
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


	# calculate a non-parametric distributional test score to rank magnitude of differences (KS Stat)

	nstats['ks_pval'] = nstats['variable'].apply(lambda x: ks_2samp(df1[x],df2[x])[1])

	print "-------------------------------------------------------------------"
	print 
	print "NUMERICAL VARIABLE COMPARISON STATS (top 25 vars)"
	print

	if len(nstats)<25:
		n_rows_print=len(nstats)
	else:
		n_rows_print=25

	print nstats[['variable','ks_pval']].sort_values('ks_pval').reset_index(drop=True)[0:n_rows_print]

	return cstats, nstats


#  add a print function for variable distribution comps ... one for num and on for cat



def num_comp_plot(n1,n2):


	return plot



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
