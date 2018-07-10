#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CHAOSS
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, 51 Franklin Street, Fifth Floor, Boston, MA 02110-1335, USA.
#
# Authors:
#     Pranjal Aswani <aswani.pranjal@gmail.com>

import os
import sys
import json
import unittest

from datetime import datetime, timezone

from elasticsearch import Elasticsearch
from elasticsearch_dsl import A

from grimoire_elk.elk import feed_backend, enrich_backend

# Hack to make sure that tests import the right packages
# due to setuptools behaviour
sys.path.insert(0, '..')

from manuscripts2.new_functions import (Query,
                                        Index,
                                        get_aggs)

# We are going to insert perceval's data into elasticsearch
# So that we can test the the functions
ES_URL = "http://127.0.0.1:9200"
INDEX_NAME = "perceval_github_test"
REPOSITORY = "https://github.com/chaoss/grimoirelab-perceval"
GIT_ENRICH_INDEX = "perceval_git_test"
GIT_RAW_INDEX = "perceval_git_test_raw"
BACKEND = "git"
BACKEND_PARAMS = [REPOSITORY]

# Some aggregation results as seen on 10th July 2018
NUM_COMMITS = 1208
NUM_AUTHORS = 19
FETCH_AGGREGATION_RESULTS_DATA1 = "data/num_hash_by_authors.json"
FETCH_SOURCE_RESULTS_DATA1 = "data/authors.json"


def load_json_file(filename, mode="r"):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename), mode) as f:
        json_content = json.load(f)
    return json_content


class TestNewFunctions(unittest.TestCase):
    """Base class to test new_functions.py"""

    maxDiff = None

    @classmethod
    def setUpClass(cls):

        cls.es = Elasticsearch(hosts=ES_URL)

        try:
            cls.es.indices.delete(index=GIT_ENRICH_INDEX)
            cls.es.indices.delete(index=GIT_RAW_INDEX)
        except Exception as e:
            print("Index doesn't exist")

        feed_backend(ES_URL, clean=True, fetch_archive=False, backend_name=BACKEND,
                     backend_params=BACKEND_PARAMS, es_index=GIT_RAW_INDEX,
                     es_index_enrich=GIT_ENRICH_INDEX, project=None, arthur=False)

        enrich_backend(ES_URL, clean=True, backend_name=BACKEND,
                       backend_params=BACKEND_PARAMS,
                       ocean_index=GIT_RAW_INDEX,
                       ocean_index_enrich=GIT_ENRICH_INDEX,
                       unaffiliated_group=None)

    def setUp(self):
        """Set up the necessary functions to run unittests"""

        self.es = Elasticsearch(ES_URL)
        self.github_index = Index(index_name=GIT_ENRICH_INDEX,
                                  es=self.es)

        self.Query_test_object = Query(self.github_index)

        self.field1 = "hash"  # field to aggregate
        self.field2 = "time_to_commit_hours"
        self.field3 = "author_name"
        self.date_field = "DATE_FIELD"  # field for range
        # Using sample filters not related to the GIT_INDEX
        self.filters = [{"item_type": "pull_request"}, {"item_type": "issue"}]
        self.offset = 2
        self.interval = "month"
        self.timezone = "UTC"
        self.start = datetime(2015, 1, 1)  # from date

        # Make sure to change the CONSTANTS defined above if you change
        # the end date here before testing because tests might fail otherwise
        self.end = datetime(2018, 7, 10)  # to date
        self.size = 10000
        self.precision_threshold = 3000

    def test_initialization(self):
        """
        Test if we can create an Query object without parameters
        """

        with self.assertRaises(TypeError):
            github_obj = Query()

        query = Query(self.github_index)

    def test_add_query(self):
        """
        Test if we can add a normal query into the search variable of Query object
        """

        # Add the query
        self.Query_test_object.add_query(self.filters[0])
        # check whether the query was inserted into the Search object or not
        self.assertDictEqual(self.Query_test_object.search.query.to_dict()['match'], {'item_type': 'pull_request'})

    def test_add_inverse_query(self):
        """
        Test if we can add a inverse query into the search variable of Query object
        """

        self.Query_test_object.add_inverse_query(self.filters[1])
        # check whether the query was inserted into the Search object or not
        self.assertDictEqual(self.Query_test_object.search.query.to_dict()['bool']['must_not'][0],
                             {'match': {'item_type': 'issue'}})

    def test_get_sum(self):
        """
        Test the sum aggregation
        """

        field = self.field1
        # without field param
        with self.assertRaises(AttributeError):
            self.Query_test_object.get_sum()

        # with field param
        self.Query_test_object.get_sum(field)
        test_agg = A("sum", field=field)
        agg_name, agg = self.Query_test_object.aggregations.popitem()
        self.assertEqual('sum_' + field, agg_name)
        self.assertEqual(agg, test_agg)

    def test_get_average(self):
        """
        Test the average aggregation
        """

        field = self.field1
        # without field param
        with self.assertRaises(AttributeError):
            self.Query_test_object.get_average()

        # with field param
        self.Query_test_object.get_average(field)
        test_agg = A("avg", field=field)
        agg_name, agg = self.Query_test_object.aggregations.popitem()
        self.assertEqual('avg_' + field, agg_name)
        self.assertEqual(agg, test_agg)

    def test_get_percentiles(self):
        """
        Test the percentiles aggregation
        """

        field = self.field1
        # without field param
        with self.assertRaises(AttributeError):
            self.Query_test_object.get_percentiles()

        # with field param
        self.Query_test_object.get_percentiles(field)
        test_agg = A("percentiles", field=field, percents=[1.0, 5.0, 25.0, 50.0, 75.0, 95.0, 99.0])
        agg_name, agg = self.Query_test_object.aggregations.popitem()
        self.assertEqual('percentiles_' + field, agg_name)
        self.assertEqual(agg, test_agg)

    def test_get_terms(self):
        """
        Test the terms aggregation
        """

        field = self.field1
        # without field param
        with self.assertRaises(AttributeError):
            self.Query_test_object.get_terms()

        # with field param
        self.Query_test_object.get_terms(field)
        test_agg = A("terms", field=field, size=self.size, order={"_count": "desc"})
        agg_name, agg = self.Query_test_object.aggregations.popitem()
        self.assertEqual('terms_' + field, agg_name)
        self.assertEqual(agg, test_agg)

    def test_get_min(self):
        """
        Test the min aggregation
        """

        field = self.field1
        # without field param
        with self.assertRaises(AttributeError):
            self.Query_test_object.get_min()

        # with field param
        self.Query_test_object.get_min(field)
        test_agg = A("min", field=field)
        agg_name, agg = self.Query_test_object.aggregations.popitem()
        self.assertEqual('min_' + field, agg_name)
        self.assertEqual(agg, test_agg)

    def test_get_max(self):
        """
        Test the max aggregation
        """

        field = self.field1
        # without field param
        with self.assertRaises(AttributeError):
            self.Query_test_object.get_max()

        # with field param
        self.Query_test_object.get_max(field)
        test_agg = A("max", field=field)
        agg_name, agg = self.Query_test_object.aggregations.popitem()
        self.assertEqual('max_' + field, agg_name)
        self.assertEqual(agg, test_agg)

    def test_get_cardinality(self):
        """
        Test the cardniality(count) aggregation
        """

        field = self.field1
        # without field param
        with self.assertRaises(AttributeError):
            self.Query_test_object.get_cardinality()

        # with field param
        self.Query_test_object.get_cardinality(field)
        test_agg = A("cardinality", field=field, precision_threshold=self.precision_threshold)
        agg_name, agg = self.Query_test_object.aggregations.popitem()
        self.assertEqual('cardinality_' + field, agg_name)
        self.assertEqual(agg, test_agg)

    def test_get_extended_stats(self):
        """
        Test the extended statistics aggregation
        """

        field = self.field1
        # without field param
        with self.assertRaises(AttributeError):
            self.Query_test_object.get_extended_stats()

        # with field param
        self.Query_test_object.get_extended_stats(field)
        test_agg = A("extended_stats", field=field)
        agg_name, agg = self.Query_test_object.aggregations.popitem()
        self.assertEqual('extended_stats_' + field, agg_name)
        self.assertEqual(agg, test_agg)

    def test_since(self):
        """
        Test the start date in range for a field
        """

        self.Query_test_object.since(start=self.start, field="closed_at")
        self.assertEqual(self.Query_test_object.range['closed_at']['gte'], self.start.isoformat())

    def test_until(self):
        """
        Test the end date in range for a field
        """

        self.Query_test_object.until(end=self.end, field="created_at")
        self.assertEqual(self.Query_test_object.range['created_at']['lte'], self.end.isoformat())

    def test_since_and_until(self):
        """
        Since the since and until functions can be for different fields, test them together
        """

        self.Query_test_object.since(start=self.start, field="closed_at")\
                              .until(end=self.end, field="closed_at")
        test_dict = {'gte': self.start.isoformat(), 'lte': self.end.isoformat()}
        self.assertDictEqual(self.Query_test_object.range['closed_at'], test_dict)

    def test_by_authors(self):
        """
        Test nested aggregation wrt authors
        """

        test_agg = A("terms", field="author_name", missing="others", size=self.size)
        test_agg.metric(0, "cardinality", field="hash", precision_threshold=self.precision_threshold)

        self.Query_test_object.get_cardinality("hash")\
                              .by_authors("author_name")
        agg_name, agg = self.Query_test_object.aggregations.popitem()

        self.assertEqual(agg, test_agg, msg='\n{0}\n{1}'.format(agg, test_agg))
        # 'msg' parameter gives us details between the dicts in case of a failure

    def test_by_organizations(self):
        """
        Test nested aggregation wrt author organizations
        """

        test_agg = A("terms", field="author_domain", missing="others", size=self.size)
        test_agg.metric(0, "cardinality", field="hash", precision_threshold=self.precision_threshold)

        self.Query_test_object.get_cardinality("hash")\
                              .by_organizations("author_domain")
        agg_name, agg = self.Query_test_object.aggregations.popitem()

        self.assertEqual(agg, test_agg, msg='\n{0}\n{1}'.format(agg, test_agg))

    def test_by_period_without_args(self):
        """
        Test the date histogram aggregation with no parameters
        """

        test_agg = A("date_histogram", field="grimoire_creation_date", interval="month", time_zone="UTC",
                     min_doc_count=0, **{})
        test_agg.metric(0, "cardinality", field=self.field1, precision_threshold=self.precision_threshold)

        self.Query_test_object.get_cardinality(self.field1)\
                              .by_period()
        agg_name, agg = self.Query_test_object.aggregations.popitem()

        self.assertEqual(agg, test_agg, msg='\n{0}\n{1}'.format(agg, test_agg))

    def test_by_period_with_params(self):
        """
        Test the date_histogram aggregation with all the parameters
        """

        start_date = self.start.replace(microsecond=0)
        start_date = start_date.replace(tzinfo=timezone.utc).timestamp()
        start_date = start_date * 1000
        end_date = self.end.replace(microsecond=0)
        end_date = end_date.replace(tzinfo=timezone.utc).timestamp()
        end_date = end_date * 1000
        bounds_dict = {"extended_bounds": {"min": start_date, "max": end_date}}

        test_agg = A("date_histogram", field="created_at", interval="week", time_zone="UTC",
                     min_doc_count=0, **bounds_dict)
        test_agg.metric(0, "cardinality", field=self.field1, precision_threshold=self.precision_threshold)

        self.Query_test_object.since(self.start)\
                              .until(self.end)\
                              .get_cardinality(self.field1)\
                              .by_period(field="created_at", period="week")

        agg_name, agg = self.Query_test_object.aggregations.popitem()

        self.assertEqual(agg, test_agg, msg='\n{0}\n{1}'.format(agg, test_agg))

    def test_multiple_aggregations(self):
        """
        Test if multiple aggregations can be added
        Choosing any 3 aggregations, randomly
        """

        self.Query_test_object.get_cardinality(self.field1)\
                              .get_sum(self.field2)\
                              .get_terms(self.field3)

        aggregations = [A("cardinality", field=self.field1, precision_threshold=3000),
                        A("sum", field=self.field2),
                        A("terms", field=self.field3, order={'_count': 'desc'}, size=10000)]

        for test_agg in aggregations[::-1]:
            agg_name, agg = self.Query_test_object.aggregations.popitem()
            self.assertEqual(agg, test_agg)

    def test_nested_aggregations(self):
        """
        Tested 3 level nested aggregation
        """

        self.Query_test_object.get_cardinality(self.field1)\
                              .by_authors()\
                              .by_period(period="quarter")

        period_agg = A("date_histogram", field="grimoire_creation_date",
                       interval="quarter", time_zone="UTC",
                       min_doc_count=0, **{})

        author_agg = A("terms", field="author_uuid", missing="others", size=self.size)

        author_agg.metric(0, "cardinality",
                          field=self.field1,
                          precision_threshold=self.precision_threshold)
        period_agg.metric(0, author_agg)

        agg_name, agg = self.Query_test_object.aggregations.popitem()
        self.assertEqual(agg, period_agg)

    def test_fetch_aggregation_results(self):
        """
        Test the fetched aggregation data
        """

        self.Query_test_object.until(end=self.end)\
                              .get_cardinality("hash")\
                              .by_authors(field="author_name")
        response = self.Query_test_object.fetch_aggregation_results()
        aggregations = {"aggregations": response['aggregations']}
        actual_response = load_json_file(FETCH_AGGREGATION_RESULTS_DATA1)

        self.assertDictEqual(aggregations, actual_response)

    def test_fetch_results_from_source(self):
        """
        Testing if specific fields can be fetched from index
        """

        self.Query_test_object.until(end=self.end)
        response = self.Query_test_object.fetch_results_from_source("author_name")
        actual_response = load_json_file(FETCH_SOURCE_RESULTS_DATA1)
        self.assertEqual(response, actual_response['hits'])

    def test_get_aggs(self):
        """
        Testing single valued aggregations
        """

        self.Query_test_object.until(end=self.end)
        self.Query_test_object.get_cardinality("hash")
        num_commits = get_aggs(self.Query_test_object)
        self.assertEqual(NUM_COMMITS, num_commits)

        self.Query_test_object.until(end=self.end)
        self.Query_test_object.get_cardinality("author_name")
        num_authors = get_aggs(self.Query_test_object)
        self.assertEqual(NUM_AUTHORS, num_authors)

    @classmethod
    def tearDownClass(cls):
        """
        Deleting the indices that were created for the tests
        """

        cls.es.indices.delete(index=GIT_ENRICH_INDEX)
        cls.es.indices.delete(index=GIT_RAW_INDEX)
