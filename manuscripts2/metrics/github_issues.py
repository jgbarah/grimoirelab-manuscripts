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

from manuscripts2.elasticsearch import Issues


class IssuesMetrics():

    def __init__(self, index):

        self.index = index

    def get_metric(self):
        raise(NotImplementedError)

    def get_section_metrics(self):

        return {
            "overview": {
                "activity_metrics": [OpenIssues(self.index), ClosedIssues(self.index)],
                "author_metrics": [],
                "bmi_metrics": [],
                "time_to_close_metrics": [],
                "projects_metrics": []
            },
            "com_channels": {
                "activity_metrics": [],
                "author_metrics": []
            },
            "project_activity": {
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
                "time_to_close_title": "Days to close (median and average)",
                "time_to_close_review_metrics": [],
                "time_to_close_review_title": "",
                "patchsets_metrics": []
            }
        }

class OpenIssues(IssuesMetrics):

    def __init__(self, index):
        super(OpenIssues, self).__init__(index)
        self.id = "opened"
        self.name = "Opened tickets"
        self.desc = "Number of opened tickets"
        self.open_issues = Issues(index)
        self.open_issues.get_cardinality("id").by_period()

    def get_metric(self):
        return self.open_issues.get_timeseries()

class ClosedIssues(IssuesMetrics):

    def __init__(self, index):
        super(ClosedIssues, self).__init__(index)
        self.id = "closed"
        self.name = "Closed tickets"
        self.desc = "Number of closed tickets"
        self.closed_issues = Issues(index).is_closed()
        self.closed_issues.get_cardinality("id").by_period()

    def get_metric(self):
        return self.closed_issues.get_timeseries()
