#!/bin/bash

# Variables for database credentials and configurations
DB_TYPE=$1
SQL_FILE="./storage/relational_db/Schema.sql"
CASSANDRA_DIR="./storage/nosql_db/cassandra_migrations/"
MONGO_DIR="./storage/nosql_db/mongodb_migrations/"
MONGO_URI="mongodb://localhost:27017"
CASSANDRA_HOST="localhost"
CASSANDRA_KEYSPACE="messages_keyspace"

# Function to perform relational database migration
migrate_relational_db() {
    echo "Starting migration for relational database..."
    if [ -f "$SQL_FILE" ]; then
        echo "Applying schema from $SQL_FILE..."
        psql -U postgres -d messaging_db -f "$SQL_FILE"
        echo "Relational database migration completed."
    else
        echo "Schema file $SQL_FILE not found."
        exit 1
    fi
}

# Function to perform MongoDB migration
migrate_mongodb() {
    echo "Starting MongoDB migration..."
    if [ -d "$MONGO_DIR" ]; then
        for file in "$MONGO_DIR"/*.js; do
            echo "Applying migration from $file..."
            mongo "$MONGO_URI" "$file"
        done
        echo "MongoDB migration completed."
    else
        echo "MongoDB migrations directory $MONGO_DIR not found."
        exit 1
    fi
}

# Function to perform Cassandra migration
migrate_cassandra() {
    echo "Starting Cassandra migration..."
    if [ -d "$CASSANDRA_DIR" ]; then
        for file in "$CASSANDRA_DIR"/*.cql; do
            echo "Applying migration from $file..."
            cqlsh "$CASSANDRA_HOST" -k "$CASSANDRA_KEYSPACE" -f "$file"
        done
        echo "Cassandra migration completed."
    else
        echo "Cassandra migrations directory $CASSANDRA_DIR not found."
        exit 1
    fi
}

# Main logic to determine which database to migrate
case $DB_TYPE in
    relational)
        migrate_relational_db
        ;;
    mongodb)
        migrate_mongodb
        ;;
    cassandra)
        migrate_cassandra
        ;;
    *)
        echo "Usage: $0 {relational|mongodb|cassandra}"
        exit 1
        ;;
esac