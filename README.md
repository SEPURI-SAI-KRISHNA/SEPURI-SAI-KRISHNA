<h1 align="center">
  <a href="https://git.io/typing-svg">
    <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=600&size=30&pause=1000&color=F7F7F7&center=true&vCenter=true&width=600&lines=Senior+Data+Engineer;Big+Data+Architect;Spark+%26+Flink+Enthusiast;Building+Scalable+Pipelines" alt="Typing SVG" />
  </a>
</h1>

<div align="center">
  <img src="https://raw.githubusercontent.com/SEPURI-SAI-KRISHNA/SEPURI-SAI-KRISHNA/output/github-contribution-grid-snake.svg" alt="snake" />
</div>

<br />

<div align="center">
  <img src="https://img.shields.io/badge/Apache%20Spark-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white" />
  <img src="https://img.shields.io/badge/Apache%20Flink-E6526F?style=for-the-badge&logo=apacheflink&logoColor=white" />
  <img src="https://img.shields.io/badge/Kafka-231F20?style=for-the-badge&logo=apachekafka&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white" />
</div>

---

### 🌊 Lambda Architecture & Data Flow

This diagram represents my standard design pattern for high-throughput ingestion using Flink (Speed Layer) and Spark (Batch Layer).

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'fontSize': '16px', 'fontFamily': 'Fira Code'}}}%%
flowchart LR
    subgraph Sources ["📡 Data Sources"]
        IoT[IoT Sensors] --> K[Apache Kafka]
        DB[(OLTP DB)] --> CDC[Debezium]
        CDC --> K
    end

    subgraph Speed ["⚡ Speed Layer (Real-time)"]
        K --> Flink[Apache Flink]
        Flink -->|Aggregations| Redis[(Redis Cache)]
        Flink -->|Stream| Hudi[Apache Hudi]
    end

    subgraph Batch ["🐢 Batch Layer (Historical)"]
        K -->|Archival| S3[Data Lake S3]
        S3 --> Spark[Apache Spark]
        Spark -->|ETL| Warehouse[(Snowflake/BigQuery)]
    end

    subgraph Serving ["🚀 Serving Layer"]
        Redis --> API[FastAPI / GraphQL]
        Warehouse --> BI[Superset / Tableau]
        Hudi --> ML[AI Model Training]
    end

    classDef source fill:#e67e22,stroke:#333,stroke-width:2px;
    classDef process fill:#2980b9,stroke:#333,stroke-width:2px;
    classDef storage fill:#27ae60,stroke:#333,stroke-width:2px;
    
    class IoT,DB,CDC source;
    class Flink,Spark,API,BI,ML process;
    class K,Redis,Hudi,S3,Warehouse storage;
    
    linkStyle default stroke:#bdc3c7,stroke-width:2px;
