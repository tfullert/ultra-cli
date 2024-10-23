import click
import pprint
import pandas as pd
from ultra_rest_client import RestApiClient

client          = None
client_username = None
client_password = None
global_verbose  = False

# -----------------------------------------------------------------------------
# Main entry point for CLI.
#
# Options:
# --username for the UltraDNS account can be specified on the command line
# --password for the UltraDNS account can be specified on the command line
#
# NOTE: You must provide a username & passsword.  If you don't use the options
# listed above then you can set these values in the shell (ex: Linux):
#
# > export ULTRA_UNAME=username
# > export ULTRA_PWORD=password
@click.group('cli-group')
@click.option('--username', 
              envvar='ULTRA_UNAME', 
              help='UltraDNS Username (can store in env).')
@click.option('--password', 
              envvar='ULTRA_PWORD', 
              help='UltraDNS Password (can store in env).')
@click.option('--verbose', 
              is_flag=True, 
              help='Display debug information.')
def cli(username, password, verbose):

    global client_username
    global client_password
    global global_verbose

    client_username = username
    client_password = password
    global_verbose  = verbose

# -----------------------------------------------------------------------------
# Command for listing aspects of an UltraDNS account
#
# Sub-commands:
# - zones
# - TODO: records 
# - TODO: users 
@cli.group('list')
def list():

    pass

# -----------------------------------------------------------------------------
# Sub-command for listing zones of an UltraDNS account
#
# Options: 
# --export the list of zones to a csv file
# -t, --type filters on type of zone (ALIAS, PRIMARY, SECONDARY)
# -n, --name filters on the name of zone (allowing for partial string matches)
# -s, --status filters on status of zone (ACTIVE, SUSPENDED)
@list.command()
@click.option('--export', 
              is_flag=True, 
              help='Export list of zones to file (csv).')
@click.option('-t', '--type', 
              required=False, 
              type=click.Choice(["ALIAS", "PRIMARY", "SECONDARY"]), 
              help='Filter on type of zone.')
@click.option('-n', '--name', 
              required=False, 
              type=str, 
              help='Search string for domain name.')
@click.option('-s', '--status', 
              required=False, 
              type=click.Choice(["ACTIVE", "SUSPENDED"]), 
              help='Filter on status of zone.')
def zones(export, type, name, status):

    global client
    global client_username
    global client_password
    global global_verbose

    client      = RestApiClient(client_username, client_password)
    pp          = pprint.PrettyPrinter(indent=4)
    cursor_info = None
    type_opt    = type
    name_opt    = name
    status_opt  = status
    zones       = {}
    query       = {}

    if name_opt:    query['name']           = name_opt
    if type_opt:    query['zone_type']      = type_opt
    if status_opt:  query['zone_status']    = status_opt

    while True:

        # Call API (support accounts with 1000+ zones using cursorInfo)
        rsp = client.get_zones_v3(q=query, limit=2, cursor=cursor_info)
        
        if global_verbose: 
            pp.pprint(rsp)
            pp.pprint(rsp['cursorInfo'])
        
        # Add zones to dict that will be used to create DataFrame 
        for zone in rsp['zones']:
            zones[zone['properties']['name']] = zone['properties']

        # If no more (i.e. not cursorInfo) then break out of loop
        if 'next' not in rsp['cursorInfo']:
            break
        
        # Check to see if there are more zones to list
        cursor_info = rsp['cursorInfo']['next']

    # Create DataFrame for display
    zone_df = pd.DataFrame.from_dict(zones, orient='index')
    #print(zone_df.sort_values(by=['resourceRecordCount']).to_string(index=False))
    print(zone_df.to_string(index=False))

    #export to CSV
    if export:
        if global_verbose: print("Output to csv file.")
        zone_df.to_csv('account.csv', index=False)

# -----------------------------------------------------------------------------
# Sub-command for listing records within a zone of the UltraDNS account
#
# Options:
# -z, --zone requires a string that identifies the zone (ex: example.com)
@list.command()
@click.option('-z', '--zone', 
              required=True, 
              type=str, 
              help='The zone to list records for.')
def records(zone):
    click.echo(f"listing records for zone {zone}.")

# -----------------------------------------------------------------------------
# Command for generating reports for the UltraDNS account
@cli.group('report')
def report():
    click.echo('report')

# -----------------------------------------------------------------------------
# Main program
if __name__ == '__main__':
    cli()
