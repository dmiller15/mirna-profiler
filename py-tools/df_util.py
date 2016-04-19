import sys

import sqlalchemy

def delete_record_from_table(unique_key_dict, table_name, engine, logger):
    unique_key_list = sorted(unique_key_dict.keys())

    statement = 'DELETE FROM ' + table_name  + ' WHERE {col} = :val0'.format(col=sorted(list(unique_key_dict.keys()))[0])
    id = 0
    for col in sorted(list(unique_key_dict.keys()))[1:]:
        id += 1
        statement += ' AND {col} = :val{id}'.format(col=col, id=id)
    kwargs = {
        'val{id}'.format(id=id): unique_key_dict[val] for id, val in enumerate(sorted(list(unique_key_dict.keys())))
        }
    logger.info('delete_record_from_table() statement=\n\t%s' % statement)
    logger.info('delete_record_from_table() kwargs=\n\t%s' % kwargs)
    stmt = sqlalchemy.sql.text(statement)
    result = engine.execute(stmt, kwargs)
    return

def save_df_to_sqlalchemy(df, unique_key_dict, table_name, engine, logger):
    logger.info('df=%s\n' % df)
    if engine.has_table(table_name):  # table already exists
        logger.info('table %s already exists' % table_name)

        delete_record_from_table(unique_key_dict, table_name, engine, logger)

        try:
            logger.info('writing sql to existing table: %s' % table_name)
            df.to_sql(table_name, engine, if_exists='append')
            logger.info('wrote sql to existing table: %s' % table_name)
        except Exception as e:
            logger.debug('exception: %s' % e)
            sys.exit(1)
    else:  # first creation of table
        logger.info('table %s does not yet exist' % table_name)
        try:
            df.to_sql(table_name, engine, if_exists='fail')
            logger.info('wrote sql to table: %s' % table_name)
        except Exception as e:
            logger.debug('exception: %s' % e)
            sys.exit(1)
