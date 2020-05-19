"""Console script for eggnog2gbk."""
import argparse
import os
from argparse import RawTextHelpFormatter
import sys
import pkg_resources
import logging
import time
from eggnog2gbk.eggnog2gbk import gbk_creation
from eggnog2gbk.utils import is_valid_dir, is_valid_file, is_valid_path

VERSION = pkg_resources.get_distribution("eggnog2gbk").version
LICENSE = """Copyright (C) Pleiade and Dyliss Inria projects
MIT License - Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions. See LICENSE for more details \n
"""
MESSAGE = """
Starting from fasta and eggnog annotation files, build a gbk file that is suitable for metabolic network reconstruction with Pathway Tools. Adds the GO terms and EC numbers annotations in the genbank file.\n
Two modes: genomic (one genome/proteome/gff/annot file --> one gbk) or metagenomic with the annotation of the full gene catalogue and fasta files (proteome/genomes) corresponding to list of genes. \n
Genomic mode can be used with or without gff files making it suitable to build a gbk from a list of genes and their annotation. \n
Examples: \n
* Genomic - single mode \n
eggnok2gbk genomic -fg genome.fna -fp proteome.faa [-gff genome.gff] -n "Escherichia coli" -o coli.gbk -a eggnog_annotation.tsv [-go go-basic.obo] \n
* Genomic - multiple mode, "bacteria" as default name \n
eggnok2gbk genomic -fg genome_dir/ -fp proteome_dir/ [-gff gff_dir/] -n bacteria -o gbk_dir/ -a eggnog_annotation_dir/ [-go go-basic.obo] \n
* Genomic - multiple mode, tsv file for organism names \n
eggnok2gbk genomic -fg genome_dir/ -fp proteome_dir/ [-gff gff_dir/] -nf matching_genome_orgnames.tsv -o gbk_dir/ -a eggnog_annotation_dir/ [-go go-basic.obo] \n
* Metagenomic \n
eggnok2gbk metagenomic -fg genome_dir/ -fp proteome_dir/ -o gbk_dir/ -a gene_cat_ggnog_annotation.tsv [-go go-basic.obo]
\n
"""

logger = logging.getLogger('eggnog2gbk')
logger.setLevel(logging.DEBUG)

def cli():
    """Console script for eggnog2gbk."""
    start_time = time.time()
    parser = argparse.ArgumentParser(
        "eggnog2gbk",
        description=MESSAGE + " For specific help on each subcommand use: eggnog2gbk {cmd} --help", formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s " + VERSION + "\n" + LICENSE)

    # parent parsers
    parent_parser_q = argparse.ArgumentParser(add_help=False)
    parent_parser_q.add_argument(
        "-q",
        "--quiet",
        dest="quiet",
        help="quiet mode, only warning, errors logged into console",
        required=False,
        action="store_true",
        default=None,
    )
    parent_parser_c = argparse.ArgumentParser(add_help=False)
    parent_parser_c.add_argument(
        "-c",
        "--cpu",
        help="cpu number for metagenomic mode or genome mode using input directories",
        required=False,
        type=int,
        default=1
    )
    parent_parser_o = argparse.ArgumentParser(add_help=False)
    parent_parser_o.add_argument(
        "-o",
        "--out",
        dest="out",
        required=True,
        help="output directory/file path",
        metavar="OUPUT_DIR"
    )
    parent_parser_faa = argparse.ArgumentParser(add_help=False)
    parent_parser_faa.add_argument(
        "-fp",
        "--fastaprot",
        help="faa file or directory",
        required=True,
        type=str
    )
    parent_parser_fna = argparse.ArgumentParser(add_help=False)
    parent_parser_fna.add_argument(
        "-fg",
        "--fastagenome",
        help="fna file or directory",
        required=True,
        type=str
    )
    parent_parser_gff = argparse.ArgumentParser(add_help=False)
    parent_parser_gff.add_argument(
        "-g",
        "--gff",
        help="gff file or directory",
        required=False,
        type=str
    )
    parent_parser_ann = argparse.ArgumentParser(add_help=False)
    parent_parser_ann.add_argument(
        "-a",
        "--annotation",
        help="eggnog annotation file or directory",
        required=True,
        type=str
    )
    parent_parser_go = argparse.ArgumentParser(add_help=False)
    parent_parser_go.add_argument(
        "-go",
        "--gobasic",
        help="go ontology, will be downloaded if not provided",
        required=False,
        default=None,
        type=str
    )
    parent_parser_name = argparse.ArgumentParser(add_help=False)
    parent_parser_name.add_argument(
        "-n",
        "--name",
        help="organism/genome name in quotes",
        required=False,
        # default="Bacteria",
        type=str
    )
    parent_parser_namef = argparse.ArgumentParser(add_help=False)
    parent_parser_namef.add_argument(
        "-nf",
        "--namefile",
        help="organism/genome name (col 2) associated to genome file basenames (col 1). Default = bacteria for all",
        required=False,
        type=str)
   # subparsers
    subparsers = parser.add_subparsers(
        title='subcommands',
        description='valid subcommands:',
        dest="cmd")
    genomic_parser = subparsers.add_parser(
        "genomic",
        help="genomic mode : 1 annot, 1 faa, 1 fna, [1 gff] --> 1 gbk",
        parents=[
            parent_parser_fna, parent_parser_faa, parent_parser_gff, parent_parser_o,
            parent_parser_ann, parent_parser_c, parent_parser_name, parent_parser_namef,
            parent_parser_go, parent_parser_q
        ],
        description=
        "Build a gbk file for each genome/set of genes with an annotation file for each"
    )
    metagenomic_parser = subparsers.add_parser(
        "metagenomic",
        help="metagenomic mode : 1 annot, n faa, n fna --> n gbk",
        parents=[
            parent_parser_fna, parent_parser_faa, parent_parser_gff, parent_parser_o, parent_parser_namef, parent_parser_name,
            parent_parser_ann, parent_parser_c, parent_parser_go, parent_parser_q
        ],
        description=
        "Use the annotation of a complete gene catalogue and build gbk files for each set of genes (fna) and proteins (faa) from input directories"
    )

    args = parser.parse_args()

    # If no argument print the help.
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # test writing in out_directory if a subcommand is given else print version and help
    if args.cmd:
        if not is_valid_path(args.out):
            logger.critical("Impossible to access/create output directory/file")
            sys.exit(1)
    else:
        logger.info("m2m " + VERSION + "\n" + LICENSE)
        parser.print_help()
        sys.exit()

    # # add logger in file
    formatter = logging.Formatter('%(message)s')
    # file_handler = logging.FileHandler(f'{args.out}/m2m_{args.cmd}.log', 'w+')
    # file_handler.setLevel(logging.INFO)
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)
    # set up the default console logger
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    if args.quiet:
        console_handler.setLevel(logging.WARNING)
    logger.addHandler(console_handler)

    # check go-basic file
    if args.gobasic and not is_valid_file(args.gobasic):
        logger.critical(f"Go-basic file path is incorrect")
        sys.exit(1)

    args = parser.parse_args()

    # check the given names
    if args.namefile and args.name:
        logger.warning("You should either use a --name or --namefile, not both. Will consider the file only.")
        orgnames = args.namefile
    elif args.namefile:
        orgnames = args.namefile
    elif args.name:
        orgnames = args.name
    else:
        orgnames = "bacteria"
        logger.warning("The default organism name 'bacteria' is used.")

    if args.cmd == "genomic":
        # fna, faa, [gff], gbk, ann must all be files or dirs, not mix of both
        types = {e: 'd' if os.path.isdir(e) else 'f' if os.path.isfile(e) else None for e in [args.fastaprot, args.fastagenome, args.annotation]}
        if args.gff:
            types[args.gff] = 'd' if os.path.isdir(args.gff) else 'f' if os.path.isfile(args.gff) else None
        if not (all(e == 'd' for e in types.values()) or all(e == 'f' for e in types.values())):
            logger.critical(f"In genomic mode, the arguments proteomes, genomes, output, annotation [and gff] must all be directories or single files but not a mix of both")
            sys.exit(1)
        else: # ensure outdir or outfile can be written
            directory_mode = True if all(e == 'd' for e in types.values()) else False
            if directory_mode and not is_valid_dir(args.out):
                logger.critical(f"Output dir path is incorrect (does not exist or cannot be written)")
                sys.exit(1)
            elif not directory_mode and not is_valid_path(args.out):
                logger.critical(f"Output file path cannot be accessed")
                sys.exit(1)
        # check names #2 
        if args.namefile and not directory_mode:
            logger.error("Tabulated file for organisms name should not be used for single runs of genomic mode. Will use the --name argument or the default 'bacteria' name if None")
            orgnames = args.name

        gbk_creation(genome=args.fastagenome, proteome=args.fastaprot, annot=args.annotation, gff=args.gff, org=orgnames, gbk=args.out, gobasic=args.gobasic, dirmode=directory_mode, cpu=args.cpu, metagenomic_mode=False)
        #TODO fix the code in case we have a gff

    elif args.cmd == "metagenomic":
        # fna, faa, gbk must all dirs and annotation must be a single file
        if not os.path.isdir(args.fastagenome) or not os.path.isdir(args.fastaprot) or not is_valid_dir(args.out) or not is_valid_file(args.annotation): 
            logger.critical(f"In metagenomic mode, proteomes, genomes, output must be directories and annotation must be a single file")
            sys.exit(1)
        gbk_creation(genome=args.fastagenome, proteome=args.fastaprot, annot=args.annotation, gff=args.gff, org=orgnames, gbk=args.out, gobasic=args.gobasic, dirmode=True, metagenomic_mode=True, cpu=args.cpu)
        
    logger.info("--- Total runtime %.2f seconds ---" % (time.time() - start_time))

if __name__ == "__main__":
    sys.exit(cli())  