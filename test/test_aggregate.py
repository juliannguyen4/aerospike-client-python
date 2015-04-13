# -*- coding: utf-8 -*-

import pytest
import sys
import cPickle as pickle
from test_base_class import TestBaseClass

try:
    import aerospike
except:
    print "Please install aerospike python client."
    sys.exit(1)

from aerospike import predicates as p


class TestAggregate(TestBaseClass):
    def setup_class(cls):
        hostlist, user, password = TestBaseClass.get_hosts()
        config = {'hosts': hostlist}
        if user == None and password == None:
            client = aerospike.client(config).connect()
        else:
            client = aerospike.client(config).connect(user, password)

        policy = {}
        client.index_integer_create('test', 'demo', 'test_age', 'age_index',
                                    policy)
        policy = {}
        client.index_integer_create('test', 'demo', 'age1', 'age_index1',
                                    policy)

        policy = {}
        filename = "stream_example.lua"
        udf_type = 0

        status = client.udf_put(filename, udf_type, policy)

        client.close()

    def teardown_class(cls):
        hostlist, user, password = TestBaseClass.get_hosts()
        config = {'hosts': hostlist}
        if user == None and password == None:
            client = aerospike.client(config).connect()
        else:
            client = aerospike.client(config).connect(user, password)
        policy = {}
        client.index_remove('test', 'age_index', policy)
        client.index_remove('test', 'age_index1', policy)
        policy = {}
        module = "stream_example.lua"

        status = client.udf_remove(module, policy)
        client.close()

    def setup_method(self, method):
        """
        Setup method.
        """

        config = {'hosts': TestBaseClass.hostlist}
        if TestBaseClass.user == None and TestBaseClass.password == None:
            self.client = aerospike.client(config).connect()
        else:
            self.client = aerospike.client(config).connect(
                TestBaseClass.user, TestBaseClass.password)

        for i in xrange(5):
            key = ('test', 'demo', i)
            rec = {
                'name': 'name%s' % (str(i)),
                'addr': 'name%s' % (str(i)),
                'test_age': i,
                'no': i
            }
            self.client.put(key, rec)

    def teardown_method(self, method):
        """
        Teardown method.
        """
        for i in xrange(5):
            key = ('test', 'demo', i)
            self.client.remove(key)
        self.client.close()

    def test_aggregate_with_no_parameters(self):
        """
            Invoke aggregate() without any mandatory parameters.
        """
        with pytest.raises(Exception) as exception:
            query = self.client.query()
            query.select()
            query.where()

        assert exception.value[0] == -2
        assert exception.value[1] == 'query() expects atleast 1 parameter'

        #assert "where() takes at least 1 argument (0 given)" in typeError.value

    def test_aggregate_no_sec_index(self):
        """
            Invoke aggregate() with no secondary index
        """
        with pytest.raises(Exception) as exception:
            query = self.client.query('test', 'demo')
            query.select('name', 'no')
            query.where(p.between('no', 1, 5))
            query.apply('stream_example', 'count')

            result = None

            def user_callback(value):
                result = value

            query.foreach(user_callback)
        assert exception.value[0] == 201L
        assert exception.value[1] == 'AEROSPIKE_ERR_INDEX_NOT_FOUND'

    def test_aggregate_with_incorrect_ns_set(self):
        """
            Invoke aggregate() with incorrect ns and set
        """
        with pytest.raises(Exception) as exception:
            query = self.client.query('test1', 'demo1')
            query.select('name', 'test_age')
            query.where(p.equals('test_age', 1))
            query.apply('stream_example', 'count')
            result = 1

            def user_callback(value):
                result = value

            query.foreach(user_callback)

        assert exception.value[0] == 4L
        assert exception.value[1] == 'AEROSPIKE_ERR_REQUEST_INVALID'

    def test_aggregate_with_where_incorrect(self):
        """
            Invoke aggregate() with where is incorrect
        """
        query = self.client.query('test', 'demo')
        query.select('name', 'test_age')
        query.where(p.equals('test_age', 165))
        query.apply('stream_example', 'count')
        records = []

        def user_callback(value):
            records.append(value)

        query.foreach(user_callback)
        assert records == []

    def test_aggregate_with_where_none_value(self):
        """
            Invoke aggregate() with where is null value
        """
        query = self.client.query('test', 'demo')
        query.select('name', 'test_age')
        with pytest.raises(Exception) as exception:
            query.where(p.equals('test_age', None))
            query.apply('stream_example', 'count')
            result = 1

            def user_callback(value):
                result = value

            query.foreach(user_callback)

        assert exception.value[0] == -2L
        assert exception.value[1] == 'predicate is invalid.'

    def test_aggregate_with_where_bool_value(self):
        """
            Invoke aggregate() with where is bool value
        """
        query = self.client.query('test', 'demo')
        query.select('name', 'test_age')
        query.where(p.between('test_age', True, True))
        query.apply('stream_example', 'count')
        records = []

        def user_callback(value):
            records.append(value)

        query.foreach(user_callback)
        assert records[0] == 1

    def test_aggregate_with_where_equals_value(self):
        """
            Invoke aggregate() with where is equal
        """
        query = self.client.query('test', 'demo')
        query.select('name', 'test_age')
        query.where(p.equals('test_age', 2))
        query.apply('stream_example', 'count')
        records = []

        def user_callback(value):
            records.append(value)

        query.foreach(user_callback)
        assert records[0] == 1

    def test_aggregate_with_empty_module_function(self):
        """
            Invoke aggregate() with empty module and function
        """
        query = self.client.query('test', 'demo')
        query.select('name', 'test_age')
        query.where(p.between('test_age', 1, 5))
        query.apply('', '')

        result = None

        def user_callback(value):
            result = value

        query.foreach(user_callback)
        assert result == None

    def test_aggregate_with_incorrect_module(self):
        """
            Invoke aggregate() with incorrect module
        """
        with pytest.raises(Exception) as exception:
            query = self.client.query('test', 'demo')
            query.select('name', 'test_age')
            query.where(p.between('test_age', 1, 5))
            query.apply('streamwrong', 'count')

            result = None

            def user_callback(value):
                result = value

            query.foreach(user_callback)

        assert exception.value[0] == -1L
        assert exception.value[1] == 'UDF: Execution Error 1'

    def test_aggregate_with_incorrect_function(self):
        """
            Invoke aggregate() with incorrect function
        """
        with pytest.raises(Exception) as exception:
            query = self.client.query('test', 'demo')
            query.select('name', 'test_age')
            query.where(p.between('test_age', 1, 5))
            query.apply('stream_example', 'countno')

            records = []

            def user_callback(value):
                records.append(value)

            query.foreach(user_callback)
        assert exception.value[0] == -1L
        assert exception.value[1] == 'UDF: Execution Error 2 : function not found'

    def test_aggregate_with_correct_parameters(self):
        """
            Invoke aggregate() with correct arguments
        """
        query = self.client.query('test', 'demo')
        query.select('name', 'test_age')
        query.where(p.between('test_age', 1, 5))
        query.apply('stream_example', 'count')

        records = []

        def user_callback(value):
            records.append(value)

        query.foreach(user_callback)
        assert records[0] == 4

    def test_aggregate_with_policy(self):
        """
            Invoke aggregate() with policy
        """
        policy = {'timeout': 1000}
        query = self.client.query('test', 'demo')
        query.select('name', 'test_age')
        query.where(p.between('test_age', 1, 5))
        query.apply('stream_example', 'count')

        records = []

        def user_callback(value):
            records.append(value)

        query.foreach(user_callback, policy)
        assert records[0] == 4

    def test_aggregate_with_extra_parameter(self):
        """
            Invoke aggregate() with extra parameter
        """
        policy = {'timeout': 1000}

        with pytest.raises(TypeError) as typeError:
            query = self.client.query('test', 'demo')
            query.select('name', 'test_age')
            query.where(p.between('test_age', 1, 5))
            query.apply('stream_example', 'count')

            result = None

            def user_callback(value):
                result = value

            query.foreach(user_callback, policy, "")

        assert "foreach() takes at most 2 arguments (3 given)" in typeError.value

    def test_aggregate_with_extra_parameters_to_lua(self):
        """
            Invoke aggregate() with extra arguments
        """
        query = self.client.query('test', 'demo')
        query.select('name', 'test_age')
        query.where(p.between('test_age', 1, 5))
        stream = None
        query.apply('stream_example', 'count', [stream])

        records = []

        def user_callback(value):
            records.append(value)

        query.foreach(user_callback)
        assert records[0] == 4

    def test_aggregate_with_extra_parameter_in_lua(self):
        """
            Invoke aggregate() with extra parameter in lua
        """
        query = self.client.query('test', 'demo')
        query.select('name', 'test_age')
        query.where(p.between('test_age', 1, 5))
        query.apply('stream_example', 'count_extra')

        records = []

        def user_callback(value):
            records.append(value)

        query.foreach(user_callback)
        assert records[0] == 4

    def test_aggregate_with_less_parameter_in_lua(self):
        """
            Invoke aggregate() with less parameter in lua
        """
        with pytest.raises(Exception) as exception:
            query = self.client.query('test', 'demo')
            query.select('name', 'test_age')
            query.where(p.between('test_age', 1, 5))
            query.apply('stream_example', 'count_less')

            records = []

            def user_callback(value):
                records.append(value)

            query.foreach(user_callback)

        assert exception.value[0] == -1L

    def test_aggregate_with_arguments_to_lua_function(self):
        """
            Invoke aggregate() with unicode arguments to lua function.
        """
        query = self.client.query('test', 'demo')
        query.where(p.between('test_age', 0, 5))
        query.apply('stream_example', 'group_count', [u"name", u"addr"])

        rec = []

        def callback(value):
            rec.append(value)

        query.foreach(callback)
        assert rec == [
            {u'name4': 1,
             u'name2': 1,
             u'name3': 1,
             u'name0': 1,
             u'name1': 1}
        ]

    def test_aggregate_with_unicode_module_and_function_name(self):
        """
            Invoke aggregate() with unicode module and function names
        """
        query = self.client.query('test', 'demo')
        query.select(u'name', 'test_age')
        query.where(p.between('test_age', 1, 5))
        query.apply(u'stream_example', u'count')

        records = []

        def user_callback(value):
            records.append(value)

        query.foreach(user_callback)
        assert records[0] == 4

    def test_aggregate_with_multiple_foreach_on_same_query_object(self):
        """
            Invoke aggregate() with multiple foreach on same query object.
        """
        query = self.client.query('test', 'demo')
        query.select('name', 'test_age')
        query.where(p.between('test_age', 1, 5))
        query.apply('stream_example', 'count')

        records = []

        def user_callback(value):
            records.append(value)

        query.foreach(user_callback)
        assert records[0] == 4

        records = []
        query.foreach(user_callback)
        assert records[0] == 4

    def test_aggregate_with_multiple_results_call_on_same_query_object(self):
        """
            Invoke aggregate() with multiple foreach on same query object.
        """
        query = self.client.query('test', 'demo')
        query.select('name', 'test_age')
        query.where(p.between('test_age', 1, 5))
        query.apply('stream_example', 'count')

        records = []
        records = query.results()
        assert records[0] == 4

        records = []
        records = query.results()
        assert records[0] == 4

    def test_aggregate_with_correct_parameters_without_connection(self):
        """
            Invoke aggregate() with correct arguments without connection
        """
        config = {'hosts': [('127.0.0.1', 3000)]}
        client1 = aerospike.client(config)

        with pytest.raises(Exception) as exception:
            query = client1.query('test', 'demo')
            query.select('name', 'test_age')
            query.where(p.between('test_age', 1, 5))
            query.apply('stream_example', 'count')

            records = []

            def user_callback(value):
                records.append(value)

            query.foreach(user_callback)

        assert exception.value[0] == 11L
        assert exception.value[1] == 'No connection to aerospike cluster'
