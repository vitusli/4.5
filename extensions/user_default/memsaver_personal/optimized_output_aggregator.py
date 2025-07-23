# copyright (c) 2018- polygoniq xyz s.r.o.

import abc
import dataclasses
import enum
import typing
import logging

logger = logging.getLogger(f"polygoniq.{__name__}")


TOptimizeDatablockResult = typing.TypeVar('TOptimizeDatablockResult', bound=enum.Enum)


@dataclasses.dataclass
class OptimizedDatablockInfo(abc.ABC, typing.Generic[TOptimizeDatablockResult]):
    name: str
    result: TOptimizeDatablockResult


TOptimizedOutput = typing.TypeVar("TOptimizedOutput", bound=OptimizedDatablockInfo)


class OptimizedOutputAggregator(abc.ABC, typing.Generic[TOptimizedOutput]):
    def __init__(self, outputs: typing.Optional[typing.List[TOptimizedOutput]] = None) -> None:
        self._outputs: typing.List[TOptimizedOutput] = [] if outputs is None else outputs

    def add_output(self, output: TOptimizedOutput) -> None:
        self._outputs.append(output)

    @abc.abstractmethod
    def _is_output_successful(self, output: TOptimizedOutput) -> bool:
        pass

    @abc.abstractmethod
    def _is_output_unchanged(self, output: TOptimizedOutput) -> bool:
        pass

    @abc.abstractmethod
    def get_output_result_message(self, output: TOptimizedOutput) -> str:
        pass

    @abc.abstractmethod
    def get_summary_message(self) -> str:
        pass

    def get_error_messages(self) -> typing.List[str]:
        error_messages = []
        for output in self.failed_outputs:
            message = self.get_output_result_message(output)
            error_messages.append(message)
        return error_messages

    @property
    def successful_outputs(self) -> typing.Iterable[TOptimizedOutput]:
        for output in self._outputs:
            if self._is_output_successful(output):
                yield output

    @property
    def unchanged_outputs(self) -> typing.Iterable[TOptimizedOutput]:
        for output in self._outputs:
            if self._is_output_unchanged(output):
                yield output

    @property
    def failed_outputs(self) -> typing.Iterable[TOptimizedOutput]:
        for output in self._outputs:
            if not (self._is_output_unchanged(output) or self._is_output_successful(output)):
                yield output


class RevertOperationResult(enum.Enum):
    SUCCESS = "Success"
    UNCHANGED = "Unchanged"
    FAILED = "Failed"


class RevertOperationResultAggregator(
    OptimizedOutputAggregator[OptimizedDatablockInfo[RevertOperationResult]]
):
    @abc.abstractmethod
    def _get_operation_target(self, plural: bool) -> str:
        pass

    def _is_output_successful(self, output: OptimizedDatablockInfo[RevertOperationResult]) -> bool:
        return output.result == RevertOperationResult.SUCCESS

    def _is_output_unchanged(self, output: OptimizedDatablockInfo[RevertOperationResult]) -> bool:
        return output.result == RevertOperationResult.UNCHANGED

    def get_output_result_message(
        self, output: OptimizedDatablockInfo[RevertOperationResult]
    ) -> str:
        RESULT_TO_MESSAGE_MAP = {
            RevertOperationResult.SUCCESS: f"{self._get_operation_target(False).capitalize()} '{output.name}' reverted to original.",
            RevertOperationResult.UNCHANGED: f"{self._get_operation_target(False).capitalize()} '{output.name}' is already original.",
            RevertOperationResult.FAILED: f"Failed to revert {self._get_operation_target(False)} '{output.name}' to original.",
        }

        message = RESULT_TO_MESSAGE_MAP.get(output.result, None)
        if message is None:
            raise ValueError(
                f"Unknown result '{output.result}' for {self._get_operation_target(False)} '{output.name}'."
            )
        return message

    def get_summary_message(self) -> str:
        messages = []
        success = sum(1 for _ in self.successful_outputs)
        if success > 0:
            messages.append(f"Reverted {success} {self._get_operation_target(success != 1)}.")
        failures = sum(1 for _ in self.failed_outputs)
        if failures > 0:
            messages.append(
                f"Failed to revert {failures} {self._get_operation_target(success != 1)}."
            )
        if len(messages) == 0:
            return "Nothing to revert."
        return " ".join(messages)
