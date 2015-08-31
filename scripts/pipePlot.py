import sys, os
import numpy as np
from numpy.random import randn
import pandas as pd
from scipy import stats
import matplotlib as mpl
mpl.use('Agg') # helps on mac --> maybe not necessary on linux? check?
import matplotlib.pyplot as plt
import seaborn as sns
import re
import argparse

#######################################################################
""" Read in Data; Set Plotting Style """
#######################################################################

parser = argparse.ArgumentParser(description="handles de_output files")
parser.add_argument('-i','--input',help='the countstable file.')
args = parser.parse_args()

reportDF=pd.io.parsers.read_table(args.input, header=0, index_col = False,sep='\t')
#reportDF=pd.io.parsers.read_table('Axolotl_no_rmdup_good_summarized_annotation.txt', header=0, index_col = False)
#reportDF=pd.io.parsers.read_table('rabbitfish_highq_rmdup_repaired_sumTrin_annotation.txt', header=0, index_col = False)
descriptions=open('/ni2/tessa_projects/build/databases/nog_categories','r')

sns.set(style="white")
sns.despine()

#######################################################################
""" Functions """
#######################################################################

def unpackListofLists(input):
    out1,out2,counts = [],[],[]
    for n in input:
        if n != '.':
            count = len(n)
        if count > 0:
            for x in n:
                out1.append(x[0])
                out2.append(x[1])
                counts.append(1/float(count))
    return out1, out2, counts

def describe(d):
    if d in nogDescriptions.keys():
        return nogDescriptions.get(d)

def categorize(f):
    if f in "DMNOTUVWYZ":
        return "CELL"
    elif f in "ABJKL":
        return "INFO"
    elif f in "CEFGHIPQ":
        return "METAB"
    elif f in "RS":
        return "POOR"
    else:
        return '.'

def getMultCogCategories(cogFunct):
    categories = []
    for c in cogFunct:
        categories.append([c, categorize(c)]) # if = '.', returns '.'
    return categories

def getColor(f,set1,set2,set3,set4):
    if f in "DMNOTUVWYZ":
        return set1.next()
    elif f in "ABJKL":
        return set2.next()
    elif f in "CEFGHIPQ":
        return set3.next()
    elif f in "RS":
        return set4.next()

def get_colors(functions, c1, c2, c3, c4):
    newPalette = []
    c1,c2,c3,c4 = iter(c1), iter(c2), iter(c3), iter(c4)
    functionList = sorted(list(functions))
    for c in functionList :
        newPalette.append(getColor(c, c1, c2, c3, c4))
    return newPalette


# PFAM
pTerms = re.compile('(PF\d*)\.\d*[\^]([^\^]*)[\^]([^\^]*)[\^]')

def getMultiplePFAMMatches(pfamEntry):
    if pfamEntry != '.':
        pfamMatches= re.findall(pTerms, pfamEntry)
        if pfamMatches is not None:
            pfam = []
            for m in pfamMatches:
                pfam= pfam + [[m[0], m[2]]] # make each entry a list
            return pfam
    else:
        return []

#######################################################################
""" COG """
#######################################################################
inCats = [ x.strip() for x in descriptions]
nogDescriptions = {line[1]:line[4:] for line in inCats if(line[:1]=='[')}
nogDescriptions['.'] = '.'
descriptions.close()



reportDF['eggNOG_function'].replace({'.':np.nan}).dropna()
cogs = list(reportDF['eggNOG_function'].map(getMultCogCategories))
cogFunctions, cogCategories, cogCounts = unpackListofLists(cogs)

cogDF = pd.DataFrame(cogFunctions, cogCategories, columns=(['Category']))
cogDF["Counts"]= cogCounts
cogDF.reset_index(level=0, inplace=True)
cogDF.rename(columns={'index': 'Description'}, inplace=True)
cogDF = cogDF.replace({'.':np.nan}).dropna()

## get Colors for Plotting COG entries
blues = sns.color_palette("Blues", 10)
greens = sns.color_palette("Greens", 8)
reds = sns.color_palette("Reds", 5)
greys = sns.color_palette("Greys", 2)
colors = get_colors(cogDF["Category"].unique(), blues, reds, greens, greys)

groupedCogDF = cogDF.groupby(["Category", "Description"], as_index=False)["Counts"].sum()
groupedCogDF['longDescription'] = groupedCogDF["Category"].map(describe)
sumCogPlot = sns.factorplot("Description", "Counts", hue="longDescription", size=6,aspect=2, data=groupedCogDF, kind='bar', palette=colors)
sumCogPlot.savefig('cogMultiple.png', format='png')
#sumCogPlot.savefig('rabbitfish_cogMultiple.png', format='png')


######### WHAT WAS I TRYING TO ACCOMPLISH HERE????? ###########
observations = pd.DataFrame(cogDF["Category"].value_counts()).sort_index()
observations = observations.rename(columns={0:"Total #"}, inPlace=True)
cogsPlusObservations = groupedCogDF.merge(observations,left_on="Category", right_index=True)
#cogsPlusObservations["% (observations/#genes)"] = 100*(cogsPlusObservations["Total #"]/numGenes)
#cogsPlusObservations["% (observations/#transcripts)"] = 100*(cogsPlusObservations["Total #"]/numTranscripts)
#cogsPlusObservations["% (observations/#nog hits)"] = 100*(cogsPlusObservations["Total #"]/numNogHits)
#cogsPlusObservations["% (category observations/#total observations)"] = 100*(cogsPlusObservations["Total #"]/cogsPlusObservations["Total #"].sum())
'''
################################################################################################
"""          PFAM            """
################################################################################################
numbers = list(reportDF['PFAM'].map(getMultiplePFAMMatches))
pfamNumb, pfamDescriptions, pfamCounts = unpackListofLists(numbers)
pfamDF = pd.DataFrame(pfamNumb, pfamDescriptions, columns=(['Family'])) #could add contig name to this DF if wanted to print..
pfamDF["Counts"]= pfamCounts
pfamDF.reset_index(level=0, inplace=True)
pfamDF.rename(columns={'index': 'Description'}, inplace=True)
newDF = pfamDF.groupby(["Family", "Description"], as_index=False)["Counts"].sum()
newDF.sort("Counts", ascending=False, inplace=True)
nDF = newDF[:21]
orderList = list(nDF["Family"])
pfamPlot = sns.factorplot("Family", "Counts", data=nDF, aspect=3, x_order= orderList, kind="bar")
#pfamPlot.savefig('pfamMultiple.png', format='png')
#nDF.to_csv('pfamTopFamilies.pfam', sep='\t', index=False) #write top families to file
pfamPlot.savefig('rabbitfish_pfamMultiple.png', format='png')
nDF.to_csv('rabbitfish_pfamTopFamilies.pfam', sep='\t', index=False) #write top families to file
#################################### END PFAM #####################################
'''
###################################################################################
""" Top KEGG entries """ #--> works for single OR multiple paths in the column
###################################################################################
keggList = [item for sublist in reportDF.Kegg_Pathway.str.split(',') for item in sublist] #make single, flat list out of the multiple-item list
pathDF = pd.DataFrame(pd.Series(keggList).value_counts()[1:]) # convert back to dataframe
pathDF.reset_index(level=0, inplace=True)
pathDF.columns = ['pathway', 'count']
pathDF = pathDF.sort('count', ascending=0)
pathXOrder = pathDF.pathway[0:20]
pathPlot = sns.factorplot('pathway', 'count', data=pathDF[0:20],aspect=3, x_order = pathXOrder)
#pathPlot.savefig('rabbitfish_keggPaths.png', format = 'png')
pathPlot.savefig('keggPaths.png', format = 'png')
#pathDF[0:20].to_csv('topKeggPaths.kegg_pathways', sep='\t', index=False) #write top paths to file
#################################### END PATHWAYS #################################
###################################################################################

###################################################################################
""" Ortholog Hit Ratio """
###################################################################################
hitRatioDF = reportDF.copy()
hitRatioDF.Sprot_BLASTX_Length = hitRatioDF.loc[:,"Sprot_BLASTX_Length"].replace({'.':np.nan})
hitRatioDF.dropna()
hitRatioDF.loc[:,("Sprot_BLASTX_Length", "Transcript_Length")] = hitRatioDF.loc[:, ("Sprot_BLASTX_Length", "Transcript_Length")].astype(float)
hitRatioDF["orthologHitRatio"] = hitRatioDF.Transcript_Length/hitRatioDF.Sprot_BLASTX_Length
data = np.array(hitRatioDF['orthologHitRatio'])
linspaceBins = np.linspace(0,2.5,num =50 )
plt.figure()
plt.hist(data,linspaceBins)
plt.title("Ortholog Hit Ratio")
plt.savefig('orthologHitRatio_moreBins.png', format='png')
#plt.savefig('rabbitfish_orthologHitRatio_moreBins.png', format='png')

###################################################################################
""" Length of blast hits vs no hits """
###################################################################################
hits =  reportDF[(reportDF.Sprot_BLASTX_Length != '.')]
hitsTranscriptLengths = np.array(hits['Transcript_Length'])
noHits = reportDF[(reportDF.Sprot_BLASTX_Length == '.')]
noHitsTranscriptLengths = np.array(noHits['Transcript_Length'])
lengthBins = np.linspace(200,1500,num =50 )
plt.figure()
plt.hist(noHitsTranscriptLengths, lengthBins, alpha =.5, label='No Hit')
if(len(hitsTranscriptLengths)>0):
    plt.hist(hitsTranscriptLengths, lengthBins,color="#F08080", alpha=.5, label='BlastX SwissProt Hit')
plt.rcParams["figure.figsize"] = (6,3.5)
plt.xlabel("Sequence Length")
plt.ylabel("Number of Sequences")
plt.legend()
plt.savefig('lengths_hits_noHits.png', format='png')
#plt.savefig('rabbitfish_lengths_hits_noHits.png', format='png')



###################################################################################
####### get basic summary stats
###################################################################################
summaryDF = reportDF.replace({'.':None})
info = {}
info['Genes'] = len(pd.unique(summaryDF["Gene_id"].dropna()))
info['Transcripts'] = len(pd.unique(summaryDF["Transcript_id"].dropna()))
info['NOG Database Hits'] =len(summaryDF["eggNOG"].dropna())
info['BLASTX hits to Swiss Prot'] = len(summaryDF["Sprot_BLASTX"].dropna())
info['BLASTP hits (ORFs) to Swiss Prot'] = len(summaryDF["Sprot_BLASTP"].dropna())
info['BLASTX hits to UniRef90'] = len(summaryDF["Uniref90_BLASTX"].dropna())
info['BLASTP hits to UniRef90'] = len(summaryDF["Uniref90_BLASTP"].dropna())
info['PFAM Domains'] =len(summaryDF["PFAM"].dropna())
info['rRNA'] = len(summaryDF['RNAMMER'].dropna())
info['predicted ORFs'] = len(summaryDF['Prot_id'].dropna())
info['BLASTX hit to "closest" species'] = len(summaryDF['Closest_BLASTX'].dropna())
info['BLASTX hit to NR'] = len(summaryDF['BLAST_NR_BestWords'].dropna())
info['Transmembrane Domains'] =  len(summaryDF['TmHMM'].dropna())
info['Signal Peptide Sequence'] = len(summaryDF['SignalP'].dropna())

infoDF = pd.DataFrame.from_dict(info.items())
infoDF.columns = ['Description', 'Number']
infoDF.to_csv('annotation.summary', sep='\t', index=False, header=False) #write top families to file
#infoDF.to_csv('rabbitfish_annotation.summary', sep='\t', index=False, header=False) #write top families to file




