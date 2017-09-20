import logging
import click


@click.command()
@click.option('--loglevel', default='INFO', help='level of logging')
def build_tree(ctx, loglevel):
    setup_logging(loglevel)

    # XXX


def setup_logging(loglevel="INFO"):
    """
    Set up logging
    :param loglevel: loglevel to use, one of ERROR, WARNING, DEBUG, INFO (default INFO)
    :return:
    """
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level,
                        format='%(levelname)s %(asctime)s %(funcName)s - %(message)s')
    logging.debug("Started log with loglevel %(loglevel)s" % {"loglevel": loglevel})
