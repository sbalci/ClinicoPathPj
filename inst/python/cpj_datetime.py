"""Explicit-format UTC calendar conversion, without locale or timezone inference."""
from datetime import datetime, timedelta, timezone
import re
import numpy as np
from cpj_runtime import Factor, InputError
from cpj_crosstable import categorical

UTC = timezone.utc
EPOCH = datetime(1970,1,1,tzinfo=UTC)
NUMERIC = {'excel_serial':datetime(1899,12,30,tzinfo=UTC),
           'excel_serial_1904':datetime(1904,1,1,tzinfo=UTC),'unix_epoch':EPOCH}
ORDERS = {'ymd':'ymd','dmy':'dmy','mdy':'mdy','ydm':'ydm','myd':'myd','dym':'dym',
          'ymdhms':'ymd','dmyhms':'dmy','mdyhms':'mdy',
          'ymdhm':'ymd','dmyhm':'dmy','mdyhm':'mdy'}
MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']
DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
COMPONENTS = ['year','month','monthname','day','hour','minute','second','dayname','weeknum','quarter','dayofyear']


def parse_value(value, fmt):
    """Return a UTC datetime; reject invalid calendars rather than rolling them over."""
    if fmt in NUMERIC:
        if isinstance(value,(bool,np.bool_)): raise ValueError('Logical values are not numeric date encodings')
        try: number=float(value)
        except (ValueError,TypeError): raise ValueError('Not a numeric encoding') from None
        if not np.isfinite(number): raise ValueError('Numeric encoding must be finite')
        seconds=number if fmt=='unix_epoch' else float(np.rint(number*86400))
        if not np.isfinite(seconds): raise ValueError('Numeric date is outside supported years 0001–9999')
        try: return NUMERIC[fmt]+timedelta(seconds=seconds)
        except (ValueError,OverflowError): raise ValueError('Numeric date is outside supported years 0001–9999') from None
    if fmt not in ORDERS: raise ValueError('Unknown explicit datetime format')
    if not isinstance(value,str): raise ValueError('Text formats require text values')
    order=ORDERS[fmt]
    fields=[r'(?P<'+c+'>'+ (r'\d{4}' if c=='y' else r'\d{1,2}') +')' for c in order]
    date_pattern=fields[0]+r'(?P<separator>[-/])'+fields[1]+r'(?P=separator)'+fields[2]
    clock=(r'[ T](?P<hour>\d{1,2}):(?P<minute>\d{2})' if fmt.endswith(('hm','hms')) else '')
    if fmt.endswith('hms'): clock+=r':(?P<second>\d{2})(?:\.(?P<fraction>\d{1,6}))?'
    suffix=r'Z?' if clock else ''
    match=re.fullmatch(date_pattern+clock+suffix,value.strip(),flags=re.ASCII)
    if match is None:
        raise ValueError('Does not match the explicit format (four-digit year; no timezone offsets)')
    parts=match.groupdict()
    try:
        return datetime(int(parts['y']),int(parts['m']),int(parts['d']),
                        int(parts.get('hour') or 0),int(parts.get('minute') or 0),int(parts.get('second') or 0),
                        int((parts.get('fraction') or '').ljust(6,'0') or 0),tzinfo=UTC)
    except ValueError: raise ValueError('Invalid calendar date or clock time') from None


def components(value):
    if value is None: return {key:None for key in COMPONENTS}
    dayofyear=(value.date()-value.date().replace(month=1,day=1)).days+1
    return dict(year=value.year,month=value.month,monthname=MONTHS[value.month-1],day=value.day,
                hour=value.hour,minute=value.minute,second=value.second+value.microsecond/1e6,
                dayname=DAYS[value.weekday()],weeknum=(dayofyear-1)//7+1,
                quarter=(value.month-1)//3+1,dayofyear=dayofyear)


def calculate(data, options):
    name=options.get('datetime_var')
    if name not in data: raise InputError('Select a datetime variable.')
    fmt=options.get('datetime_format','ymd')
    if fmt not in set(ORDERS)|set(NUMERIC): raise InputError('Choose a supported explicit datetime format.')
    if options.get('timezone','UTC')!='UTC': raise InputError('This explicit-format core supports UTC only.')
    limit=options.get('preview_rows',20)
    if isinstance(limit,bool) or not isinstance(limit,int) or not 10<=limit<=100:
        raise InputError('Preview rows must be an integer from 10 to 100.')
    column=data[name]
    metadata=getattr(data,'metadata',{}).get(name,{})
    if metadata.get('dimensions') or set(metadata.get('classes') or [])-{'numeric','integer','factor','ordered','character'}:
        raise InputError('Select scalar text, nominal/ordinal or numeric encodings; native Date/POSIX and custom classes require explicit conversion first.')
    if isinstance(column,Factor):
        codes,labels=categorical(column,name)
        values=[None if v<0 else labels[v] for v in codes]
    elif isinstance(column,np.ndarray) and column.ndim==1 and column.dtype.kind in 'fiu':
        if fmt not in NUMERIC: raise InputError('For a numeric column choose Excel 1900, Excel 1904 or Unix epoch explicitly.')
        values=[None if np.isnan(v) else float(v) for v in column]
    elif isinstance(column,list) and all(v is None or isinstance(v,str) for v in column): values=column
    else: raise InputError('Select a scalar text, nominal/ordinal or numeric datetime encoding.')
    if not 1<=len(values)<=10000: raise InputError('The datetime core accepts one to 10,000 rows without sampling.')
    rows=[];dates=[];epochs=[];counts={'parsed':0,'invalid':0,'missing':0};early=0
    for value in values:
        display=None if value is None else str(value)
        if value is None or isinstance(value,str) and not value.strip():
            date=None;status='Missing';reason='Missing or blank input';counts['missing']+=1
        else:
            try:
                date=parse_value(value,fmt);status='Parsed';reason='Explicit format; UTC';counts['parsed']+=1
                if fmt=='excel_serial' and float(value)<61:
                    early+=1;reason='Parsed using 1899-12-30 origin; early Excel convention'
            except ValueError as error:
                date=None;status='Invalid';reason=str(error);counts['invalid']+=1
        dates.append(date)
        epoch=None if date is None else (date-EPOCH).total_seconds()
        epochs.append(epoch)
        corrected=None if date is None else date.isoformat(timespec='microseconds' if date.microsecond else 'seconds').replace('+00:00','Z')
        rows.append(dict(original=display,corrected=corrected,status=status,reason=reason,**components(date)))
    nonmissing=len(values)-counts['missing']
    return dict(rows=rows,dates=dates,epoch=epochs,total=len(values),**counts,
                success=counts['parsed']/nonmissing if nonmissing else None,early_excel=early,
                minimum=min((v for v in epochs if v is not None),default=None),
                maximum=max((v for v in epochs if v is not None),default=None),fmt=fmt,preview_limit=limit)
