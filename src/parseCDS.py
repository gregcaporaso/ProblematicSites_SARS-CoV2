#!/usr/local/bin/python

from BCBio import GFF
from Bio import SeqIO
from Bio.Alphabet import IUPAC
from copy import copy
from Bio.Seq import Seq

#%%

def readGFF(gff):

    with open(gff, 'r') as gff_file:
        for rec in GFF.parse(gff_file, limit_info=dict(gff_type = ["gene"])):
            genes = rec.features
    return genes


def readFA(fa):
    proteins = dict()
    record_dict = SeqIO.to_dict(SeqIO.parse(fa, "fasta"))
    for id, vals in record_dict.items():
        name = record_dict[id].description.split(' ')[1][1:-1].replace('=', '-')
        proteins[name] = vals.seq
    return proteins



def readFasta(fasta):
    with open(fasta, 'r') as fa:
        for line in fa:
            if not line.startswith('>'):
                return line


def getCodonPos(pos, gene_start):
    mod = (pos - gene_start + 2) / 3
    rest = round(mod % 1, 1)
    if rest == 0:
        codon_pos = 0
    elif rest == 0.3:
        codon_pos = 1
    elif rest == 0.7:
        codon_pos = 2
    else:
        print("codon pos not determined")
        codon_pos = 'NA'
    return codon_pos


def getCodon(genome, pos, codon_pos):
    # convert from 1 based
    pos -= 1
    if codon_pos == 0:
        codon = genome[pos: pos + 3]
    elif codon_pos == 1:
        codon = genome[pos - 1: pos + 2]
    elif codon_pos == 2:
        codon = genome[pos - 2: pos + 1]
    else:
        print("broken codon")

    if len(codon) != 3:
        print("weird codon")

    return codon


def getAltAA(codon, codon_pos, alt_nuc):
    # produce all combos
    pot_codon = []
    for n in alt_nuc:
        codon_copy = list(copy(codon))
        codon_copy[codon_pos] = n
        pot_codon.append(''.join(codon_copy))

    alt_AAs = []
    for c in pot_codon:
        cod = Seq(c, IUPAC.ambiguous_dna)
        alt_aa = cod.translate()
        alt_AAs.append(str(alt_aa))

    alt_AAs = ','.join(alt_AAs)
    return alt_AAs


def main():
    # parse gff
    gff = "data/MN908947_3.gff3"
    vcf = "problematic_sites_sarsCov2.vcf"
    prot = "data/MN908947_3.prot.fa"
    fasta = "data/SARS-CoV-2.fa.unwrapped"
    genes = readGFF(gff)
    proteins = readFA(prot)
    genome = readFasta(fasta)


    vcf_rebuild = []
    with open(vcf, 'r') as vcf_file:
        for line in vcf_file:
            if not line.startswith('#'):
                vcf_line = line.rstrip('\n').split('\t')
                pos = int(vcf_line[1])

                ingene = False
                for gene in genes:
                    if gene.location.nofuzzy_start <= pos <= gene.location.nofuzzy_end:
                        gene_start = gene.location.nofuzzy_start
                        vcf_aa = str(int((pos - gene_start + 2) / 3))
                        codon_pos = getCodonPos(pos=pos, gene_start=gene_start)
                        codon = getCodon(genome=genome, pos=pos, codon_pos=codon_pos)
                        alt_nuc = vcf_line[4].split(',')
                        alt_aa = getAltAA(codon=codon, codon_pos=codon_pos, alt_nuc=alt_nuc)

                        vcf_line[10] = gene.id                                  # gene name
                        vcf_line[11] = vcf_aa                                   # aa position
                        vcf_line[12] = proteins[gene.id][int(vcf_aa) - 1]       # reference aa
                        vcf_line[13] = alt_aa                                      # alternative aa
                        ingene = True
                        break

                if not ingene:
                    vcf_line[10] = '.'  # gene name
                    vcf_line[11] = '.'  # aa position
                    vcf_line[12] = '.'  # reference aa
                    vcf_line[13] = '.'  # alternative aa

                vcf_rebuild.append("\t".join(vcf_line))

            else:
                vcf_rebuild.append(line.rstrip('\n'))

    # write updated VCF
    with open("problematic_sites_sarsCov2_genes.vcf", "w") as out_file:
        for line in vcf_rebuild:
            out_file.write(line + "\n")
            # pass


if __name__ == "__main__":
    main()