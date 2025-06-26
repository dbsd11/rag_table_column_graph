# rag_table_column_graph
rag on database table column graph

## design

1. [graphiti](https://github.com/getzep/graphiti)
   * based on graphiti to add episodes, table column nodes, and embedings

## useage

start

```
python -m notebook
# browser open rag_graphiti.ipynb to run the demo
```


dependency
-- download [apoc](https://neo4j.com/docs/apoc/current/installation/#apoc) jar to .\neo4j\plugin.

* neo4j
  ```
    docker run -tid --name neo4j -p7474:7474 -p7687:7687 -v .\neo4j\data:/data -v .\neo4j\plugins:/var/lib/neo4j/plugins -v .\neo4j\import:/var/lib/neo4j/import -v .\neo4j\logs:/logs -e NEO4J_AUTH=neo4j/test1234 -e NEO4J_dbms_security_procedures_unrestricted=apoc.* -e NEO4J_dbms_security_procedures_allowlist=apoc.* docker.xuanyuan.me/library/neo4j:latest
  ```
