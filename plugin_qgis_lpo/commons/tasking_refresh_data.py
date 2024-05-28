from functools import partial

from qgis.core import (
    QgsApplication,
    QgsMessageLog,
    QgsProcessingAlgRunnerTask,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProject,
    QgsTaskManager,
)

from ..toolbelt.log_handler import PlgLogger

MESSAGE_CATEGORY = "AlgRunnerTask"

logger = PlgLogger().log


def task_finished(_context, successful, _results):
    if not successful:
        logger.log(
            message=str("Task finished unsucessfully"),
            log_level=2,
            push=True,
            duration=2,
        )
    else:
        logger.log(
            message=str("Task finished successfully"),
            log_level=0,
            push=True,
            duration=2,
        )


def bg_task(algorithm: str, params: dict):
    alg = QgsApplication.processingRegistry().algorithmById(algorithm)

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    task = QgsProcessingAlgRunnerTask(alg, params, context, feedback)

    task.executed.connect(partial(task_finished, context))
    return task
