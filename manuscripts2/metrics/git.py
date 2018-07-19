#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Author:
#   Pranjal Aswani <aswani.pranjal@gmail.com>
#

from manuscripts2.elasticsearch import Query


class GitMetrics():

    def __init__(self, index):

        self.commits = Query(index)
        self.index = index

    def get_metric(self):
        raise(NotImplementedError)

    def get_section_metrics(self):

        return {
            "overview": {
                "activity_metrics": [Commits(self.index)],
                "author_metrics": [Authors(self.index)],
                "bmi_metrics": [],
                "time_to_close_metrics": [],
                "projects_metrics": []
            },
            "com_channels": {
                "activity_metrics": [],
                "author_metrics": []
            },
            "project_activity": {
                # TODO: Authors is not activity but we need two metrics here
                "metrics": []
            },
            "project_community": {
                "author_metrics": [],
                "people_top_metrics": [],
                "orgs_top_metrics": [],
            },
            "project_process": {
                "bmi_metrics": [],
                "time_to_close_metrics": [],
                "time_to_close_title": "",
                "time_to_close_review_metrics": [],
                "time_to_close_review_title": "",
                "patchsets_metrics": []
            }
        }

class Commits(GitMetrics):

    def __init__(self, index):
        super(Commits, self).__init__(index)
        self.id = "commits"
        self.name = "Commits"
        self.desc = "Changes to the source code"
        self.commits.get_cardinality("hash").by_period()

    def get_metric(self):
        return self.commits.get_timeseries()

class Authors(GitMetrics):

    def __init__(self, index):
        super(Authors, self).__init__(index)
        self.id = "authors"
        self.name = "Authors"
        self.desc = "People authoring commits (changes to source code)"
        self.commits.get_cardinality("author_uuid").by_period()

    def get_metric(self):
        return self.commits.get_timeseries()
