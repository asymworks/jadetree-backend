"""Jade Tree Custom Marshmallow Fields.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

import typing

import marshmallow as ma


class DelimitedList(ma.fields.List):
    """A field which is similar to a List, but takes its input as a delimited string (e.g. "foo,bar,baz").

    Like List, it can be given a nested field type which it will use to
    de/serialize each element of the list.

    :param Field cls_or_instance: A field class or instance.
    :param str delimiter: Delimiter between values.
    """
    # Most of this class is adapted from webargs
    # https://github.com/marshmallow-code/webargs/blob/dev/src/webargs/fields.py

    delimiter: str = ','

    def __init__(
        self,
        cls_or_instance: typing.Union[ma.fields.Field, type],
        *,
        delimiter: typing.Optional[str] = None,
        **kwargs
    ):
        """Class constructor."""
        self.delimiter = delimiter or __class__.delimiter
        super().__init__(cls_or_instance, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        # serializing will start with parent-class serialization, so that we correctly
        # output lists of non-primitive types, e.g. DelimitedList(DateTime)
        return self.delimiter.join(
            format(each) for each in super()._serialize(value, attr, obj, **kwargs)
        )

    def _deserialize(self, value, attr, data, **kwargs):
        dsValue = value
        if isinstance(dsValue, list):
            # marshmallow likes to infer a single-element list
            dsValue = value[0]

        # attempting to deserialize from a non-string source is an error
        if not isinstance(dsValue, (str, bytes)):
            raise ma.ValidationError('Invalid delimited list')
        return super()._deserialize(dsValue.split(self.delimiter), attr, data, **kwargs)
