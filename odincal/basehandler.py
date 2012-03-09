import pg
import ctypes
class BaseHandler(object):
    def __init__(self,primary_key):
        self.pk = primary_key

    def insert_statement(self):
        query = 'insert into {} ('.format(
            self.data_fields.__class__.__name__)
        columns = []
        for i in self.data_fields._fields_:
            if i[0].startswith('no'):
                pass
            else:
                columns.append('{} '.format(i[0]))
        if hasattr(self,'extra_data_field'):
            columns.append('{}'.format(self.extra_data_field))
        query += ', '.join(columns)
        query += ') values ('
        values = []
        for i in self.data_fields._fields_:
            if i[0].startswith('no'):
                pass
            elif i[1].__base__ == ctypes.Array:
                values.append("'{}'".format(
                    pg.escape_bytea(getattr(self.data_fields,i[0]))))
            elif i[1].__name__ in ('c_short','c_ushort','c_int','c_uint'):
                values.append('{}'.format(getattr(self.data_fields,i[0])))
            pass
        if hasattr(self,'extra_data_field'):
            values.append("'{}'".format(pg.escape_bytea(getattr(
                self,self.extra_data_field).data)))
        query += ', '.join(values)
        query += ')'
        return query

    def create_statement(self, temporary=False):
        tmpstatement = ''
        if temporary:
            tmpstatement =' temporary'
        query = 'create{} table {} ('.format(
            tmpstatement, self.data_fields.__class__.__name__)
        columns = []
        for i in self.data_fields._fields_:
            if i[0].startswith('no'):
                pass
            elif i[1].__base__ == ctypes.Array:
                columns.append('{} bytea'.format(i[0]))
            elif i[1].__name__ in ('c_short',):
                columns.append('{} smallint'.format(i[0]))
            elif i[1].__name__ in ('c_ushort','c_int'):
                columns.append('{} integer'.format(i[0]))
            elif i[1].__name__ in ('c_uint',):
                columns.append('{} bigint'.format(i[0]))
            pass
        if hasattr(self,'extra_data_field'):
            columns.append('{} bytea'.format(self.extra_data_field))
        query += ','.join(columns)
        query += ',constraint {} primary key ({})'.format(
            'pk_'+self.data_fields.__class__.__name__, ','.join(self.pk))
        query += ')'
        return query

    def __repr__(self):
        output =""
        for i in self.data_fields._fields_:
            if i[0].startswith('no'):
                continue
            elif i[1].__base__ == ctypes.Array:
                output += ' {0:<12}:{1:}\n'.format(
                    i[0],str(getattr(self.data_fields,i[0])))
            else:
                output += ' {0:<12}:{1:x}\n'.format(
                    i[0],getattr(self.data_fields,i[0]))
        return output


