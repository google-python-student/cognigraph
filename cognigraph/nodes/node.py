import time
import numpy as np
from typing import Tuple

from ..helpers.misc import class_name_of


class Node(object):
    """ Any processing step (including getting and outputting data) is an instance of this class.
    This is an abstract class.
    """

    @property
    def CHANGES_IN_THESE_REQUIRE_RESET(self) -> Tuple[str]:
        """A constant tuple of attributes after a change in which a reset should be scheduled."""
        msg = 'Each subclass of Node must have a CHANGES_IN_THESE_REQUIRE_RESET constant defined'
        raise NotImplementedError(msg)

    @property
    def UPSTREAM_CHANGES_IN_THESE_REQUIRE_REINITIALIZATION(self) -> Tuple[str]:
        """A constant tuple of attributes after an *upstream* change in which an initialization should be scheduled."""
        msg = 'Each subclass of Node must have a CHANGES_IN_THESE_REQUIRE_REINITIALIZATION constant defined'
        raise NotImplementedError(msg)

    def __init__(self):
        self.input_node = None  # type: Node
        self.output = None  # type: np.ndarray
        
        self.there_has_been_a_change = False  # This is used as a message to the next node telling it that either this 
        # or one of the node before had a significant change
        self._should_initialize = True
        self._should_reset = False
        self._saved_from_upstream = None  # type: dict  # Used to determine whether upstream changes warrant
        # reinitialization

    def initialize(self):
        self._saved_from_upstream = {item: self.traverse_back_and_find(item) for item
                                     in self.UPSTREAM_CHANGES_IN_THESE_REQUIRE_REINITIALIZATION}
        self._initialize()

    def _initialize(self):
        raise NotImplementedError

    def __setattr__(self, key, value):
        self._check_value(key, value)
        if key in self.CHANGES_IN_THESE_REQUIRE_RESET:
            self._should_reset = 1
            self.there_has_been_a_change = True  # This is a message for the next node
        super().__setattr__(key, value)

    def _check_value(self, key, value):
        raise NotImplementedError

    def update(self) -> None:
        self.output = None  # Reset output in case update does not succeed

        if self._there_was_a_change_upstream():
            self._react_to_the_change_upstream()  # Schedule reset or initialize
        self._reset_or_reinitialize_if_needed()  # Needed - because of a possible change in this node or upstream

        self._update()

    def _update(self):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError
        
    def traverse_back_and_find(self, item: str):
        """ This function will walk up the node tree until it finds a node with an attribute <item> """
        try:
            return getattr(self.input_node, item)
        except AttributeError:
            try:
                return self.input_node.traverse_back_and_find(item)
            except AttributeError:
                msg = 'None of the predecessors of a {} node contains attribute {}'.format(
                    class_name_of(self), item)
                raise AttributeError(msg)

    def _there_was_a_change_upstream(self):
        """Asks the immediate predecessor node if there has a been a change in or before it"""
        if self.input_node is not None and self.input_node.there_has_been_a_change is True:
            return True
        else:
            return False

    def _react_to_the_change_upstream(self):
        """Schedules reset or reinitialization of the node depending on what has changed."""
        if self._the_change_requires_reinitialization():
            self._should_initialize = True
        else:
            self._should_reset = True

        self.input_node.there_has_been_a_change = False  # We got the message, no need to keep telling us.
        self.there_has_been_a_change = True  # We should however leave a message to the node after us.

    def _reset_or_reinitialize_if_needed(self):
        if self._should_initialize is True:
            self.initialize()
        elif self._should_reset is True:
            self.reset()
        self._should_initialize = False
        self._should_reset = False

    def _the_change_requires_reinitialization(self):
        for item, value in self._saved_from_upstream.items():
            if value != self.traverse_back_and_find(item):
                return True
        return False


class SourceNode(Node):
    """ Objects of this class read data from a source """

    # There is no 'upstream' for the sources
    UPSTREAM_CHANGES_IN_THESE_REQUIRE_REINITIALIZATION = ()

    def __init__(self, seconds_to_live=None):
        super().__init__()
        self.frequency = None
        self.dtype = None
        self.channel_count = None
        self.channel_labels = None
        self.source_name = None

        # TODO: remove this self-destruction nonsense
        self._should_self_destruct = seconds_to_live is not None
        if self._should_self_destruct:
            self._birthtime = None
            self._seconds_to_live = seconds_to_live
            self._is_alive = True

    @property
    def is_alive(self):
        # TODO: remove this self-destruction nonsense
        if self._should_self_destruct:
            current_time_in_s = time.time()
            if current_time_in_s > self._birthtime + self._seconds_to_live:
                self._is_alive = False
        return self._is_alive

    def _initialize(self):
        if self._should_self_destruct:
            self._birthtime = time.time()

    def _update(self):
        super()._update()


class ProcessorNode(Node):
    pass  # TODO: implement


class OutputNode(Node):
    pass  # TODO: implement
