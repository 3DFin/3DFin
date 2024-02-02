import sys
import typing


class Progress(object):
    """A simple progress bar implementation."""

    title: str
    n_chars: int
    output: typing.TextIO
    progress_char: str = "█"
    void_char: str = "░"

    def __init__(
        self, title="Progress", n_chars: int = 60, output: typing.TextIO = sys.stdout
    ):
        """Construct a progress bar object.

        A simple progress bar taylored for our needs. It is intended to be used with dendromatics.
        The progress bar update() method should to be passed to dendromatics function that optionally
        take a process hook.

        Parameters
        ----------
        title : str
            The title of the progress bar
        n_chars : int
            The number of characters to use in the progress bar (the length of the progress bar).
        output : typing.TextIO
            File like object

        """
        self.title = title
        self.n_chars = n_chars
        self.output = output

    def _start(self, total: int) -> None:
        """Start the progress bar.

        Parameters
        ----------
        total : int
            The total number of steps to be completed.

        """
        self.output.write(
            f"\n{self.title} [{(self.void_char * self.n_chars)}] 0/{total}"
        )
        self.output.flush()

    def _finish(self, total: int) -> None:
        """Terminate the progress bar.

        Parameters
        ----------
        total : int
            The total number of steps to be completed.

        """
        self.output.write(
            f"\r{self.title} [{(self.progress_char * self.n_chars)}] {total}/{total}"
        )
        self.output.flush()
        self.curr_progress = 0
        self.output.write("\n")
        self.output.flush()

    def update(self, count: int = 1, total: int = 1) -> None:
        """Update the progress bar with a given count.

        If count is equal to 0, the progress bar is started.
        If count is equal to total, the progress bar is finished.

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
            f"\r{self.title} [{(self.progress_char * progress)}{(self.void_char * (self.n_chars - progress))}] {count}/{total}"
        )
        self.output.flush()
        return None
