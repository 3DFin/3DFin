import sys
import typing

from three_d_fin.processing.progress import Progress


class CloudCompareProgress(Progress):
    """A simple progress bar implementation taylored for CloudCompare Plugin.

    CloudCompare console does not support CR char so this implementation tends
    to replace it with LF. It induce a less esthetic multiline progress than the
    proper render in TTY.

    CloudCompare console is making auto flush at regular interval thus manual flushing
    is not necessary.
    """

    def _start(self, total: int):
        """Start the progress bar.

        Parameters
        ----------
        total : int
            The total number of steps to be completed.
        """
        self.curr_progress = 0
        self.output.write(
            f"\n{self.title} [{(self.void_char * self.n_chars)}] 0/{total}"
        )

    def _finish(self, total: int):
        """Terminate the progress bar.

        Parameters
        ----------
        total : int
            The total number of steps to be completed.
        """
        self.output.write(
            f"\n{self.title} [{(self.progress_char * self.n_chars)}] {total}/{total}"
        )
        self.curr_progress = 0
        self.output.write("\n")

    def update(self, count: int = 1, total: int = 1) -> None:
        """Update the progress bar with a given count.

        If count is equal to 0, the progress bar is started.
        If count is equal to total, the progress bar is finished.
        Only refresh if the progress bar has advanced (count % (total * n_chars) == 0

        Parameters
        ----------
        count : int
            The number of steps already completed.
        total : int
            The total number of steps to be completed.
        """
        if count > total or count < 0:
            raise ValueError("count cannot be greater than total nor less than 0")
        if count == 0:
            return self._start(total)
        if count == total:
            return self._finish(total)
        progress = int(count / total * self.n_chars)
        self.output.write(
            f"\n{self.title} [{(self.progress_char * progress)}{(self.void_char * (self.n_chars - progress))}] {count}/{total}"
        )
        return None
