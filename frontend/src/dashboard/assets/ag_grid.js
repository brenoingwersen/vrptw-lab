var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.StatusBadge = function (props) {
    const {setData, data} = props;

    function onClick() {
        setData();
    }

    const statusColors = {
        queued: 'bg-secondary',
        running: 'bg-warning text-dark',
        completed: 'bg-success',
        failed: 'bg-danger',
    };

    const color = statusColors[data.status] || 'bg-secondary';

    return React.createElement(
        'span',
        {
            onClick: onClick,
            className: `badge ${color}`,
        },
        props.value
    );
};
