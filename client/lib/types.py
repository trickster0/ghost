#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import enum

class EventLogType( enum.IntEnum ):
    INFO    = 0
    GOOD    = 1
    ERROR   = 2
