# wiki-es-dump
A small repository of code processing raw wiki files into easy-to-understand format using PySpark

## Requirements
- Java 8 is required for running PySpark
- pyspark for multi-thread processing
- mwparserfromhell for parsing WikiCode
- elasticsearch for defining and uploading the indices

## Storage Requirements
This processing script requires at least 250G of storage space (not counting scratch space for Spark).
All intermediate files will be stored at the same directory as the raw data files. 
These files are created in case unexpected errors happen and users can recover quickly.
These files needs to be manually deleted after the processing is done. 

## Usage

1. First, run the preprocess.py file using spark. Example:

```
SPARK_SCRATCH_DIR = '/absolute/path/to/large/scratch_dir'
JAVA_HOME = '/path/to/java/home
DUMP_PATH = '/absolute/path/to/wikipedia_dump'
PAGEVIEW_PATH = '/absolute/path/to/wikipedia_pageview'
WIKIDATA_PATH = '/absolute/path/to/wikidata

spark-submit \
    --conf spark.local.dir=SPARK_SCRATCH_DIR \
    --driver-memory 50G \
    preprocess.py \
    DUMP_PATH PAGEVIEW_PATH WIKIDATA_PATH 24
```

Note:
- Spark scratch directory is optional, but on some machines the scratch directory is not large enough 
for spark, and thus need to be manually set
- Java home is also optional, but on some machines spark has a hard time finding the right runtime.

2. Next, start an interactive shell and use the contents of define_es.py to define the indices with the correct
mapping. Alternatively, you can run `python define_es.py --help` for usage information

3. Run `python upload.py --help` to see the description of upload script usage, and use `spark-submit` similar
to step 1 to upload your processed files into elastic search