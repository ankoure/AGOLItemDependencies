import arcpy, json
from arcgis.gis import GIS

# Variables
portal = arcpy.GetParameterAsText(0)
username = arcpy.GetParameterAsText(1)
password = arcpy.GetParameterAsText(2)
sourceUser = arcpy.GetParameterAsText(3)
contentType = arcpy.GetParameterAsText(4)
items = arcpy.GetParameterAsText(5)
csv_output = arcpy.GetParameterAsText(6)

arcpy.env.overwriteOutput = 1

startTime = time.time()

# Create GIS object
gis = GIS(portal, username, password, verify_cert=False)

# Function to check web applications for web map ID
def checkWebApps(webMapID, dependencies):
    # Get all users
    sourceUserList = []
    source_users = gis.users.search(max_users=100000)
    for user in source_users:
        if user.user_types()['name'] not in ('Viewer', 'Editor', 'Field Worker'):
                sourceUserList.append(user.username)

    # Search Web AppBuilder and Instant Apps for each user
    for user in sourceUserList:
        searchResults = gis.content.search(query=f"owner:{user}", item_type="Web Mapping Application", max_items = 500)
        if len(searchResults) > 0:
           # iterate results JSON
           for result in searchResults:
               webAppID = result['id']
               webApp = gis.content.get(webAppID)
               webAppTitle = webApp.title
               webAppDict = webApp.get_data(try_json=True)
               webAppJSON = json.dumps(webAppDict)
               try:
                   if 'Code Sample' not in webApp.typeKeywords:
                       if webMapID in webAppJSON:
                               dependencies = True
                               arcpy.AddMessage(f"--Web Map used in {webAppTitle}")
                               if contentType == 'Services':
                                   output = '{0},{1},{2},{3},{4},{5}\n'.format(item.title, item.id, webmap.title,
                                                                               webmap.id, webAppTitle, webAppID)
                               elif contentType == 'Web Maps':
                                   output = '{0},{1},{2},{3}\n'.format(item.title, item.id, webAppTitle, webAppID)
                               output_file.write(output)
               except Exception as e:
                    pass

        # Experience Builder Apps
        searchResults = gis.content.search(query=f"owner:{user}", item_type="Web Experience", max_items=500)
        if len(searchResults) > 0:
            # iterate results JSON
            for result in searchResults:
                webAppID = result['id']
                webApp = gis.content.get(webAppID)
                webAppDict = webApp.get_data(try_json=True)
                webAppJSON = json.dumps(webAppDict)
                try:
                    if webMapID in webAppJSON:
                        dependencies = True
                        webAppTitle = webApp.title
                        arcpy.AddMessage(f"--Web Map used in {webAppTitle}")
                        if contentType == 'Services':
                            output = '{0},{1},{2},{3},{4},{5}\n'.format(item.title, item.id, webmap.title,
                                                                        webmap.id, webAppTitle, webAppID)
                        elif contentType == 'Web Maps':
                            output = '{0},{1},{2},{3}\n'.format(item.title, item.id, webAppTitle, webAppID)
                        output_file.write(output)
                except Exception as e:
                    pass

        # Dashboards
        searchResults = gis.content.search(query=f"owner:{user}", item_type="Dashboard", max_items=500)
        if len(searchResults) > 0:
            # iterate results JSON
            for result in searchResults:
                webAppID = result['id']
                webApp = gis.content.get(webAppID)
                webAppDict = webApp.get_data(try_json=True)
                webAppJSON = json.dumps(webAppDict)
                if webMapID in webAppJSON:
                    dependencies = True
                    webAppTitle = webApp.title
                    arcpy.AddMessage(f"--Web Map used in {webAppTitle}")
                    if contentType == 'Services':
                        output = '{0},{1},{2},{3},{4},{5}\n'.format(item.title, item.id, webmap.title,
                                                                    webmap.id, webAppTitle, webAppID)
                    elif contentType == 'Web Maps':
                        output = '{0},{1},{2},{3}\n'.format(item.title, item.id, webAppTitle, webAppID)
                    output_file.write(output)

    return dependencies

# Create and open CSV file with the option to append data
output_file = open(csv_output, 'w')

# Write CSV file header
if contentType == 'Services':
   header = 'SERVICE NAME,SERVICE ID,WEB MAP NAME,WEB MAP ID,WEB APP NAME,WEB APP ID\n'
elif contentType == 'Web Maps':
   header = 'WEB MAP NAME,WEB MAP ID,WEB APP NAME,WEB APP ID\n'
output_file.write(header)

# Find item dependencies
for item in items.split(';'):
    itemID = (item.split(' - ')[2])
    if itemID[-1] == "'":
        itemID = itemID[0:-1]
    elif itemID[-1] == '"':
        itemID = itemID[0:-1]
    item = gis.content.get(itemID)
    itemURL = item.url
    arcpy.AddMessage("==========================")
    arcpy.AddMessage("Processing {0}".format(item.title))
    if contentType == 'Services':
        # Create variable set to False, this will update to True if
        # service exists in any web map
        webMapDependent = False
        # Create list of all users that can own web maps
        sourceUserList = []
        source_users = gis.users.search(max_users=100000)
        for user in source_users:
            if user.user_types()['name'] not in ('Viewer', 'Editor', 'Field Worker'):
                    sourceUserList.append(user.username)
        # Iterate through list of user's web maps and check if service id/url exists
        for user in sourceUserList:
            searchResults = gis.content.search(query=f"owner:{user}", item_type="Web Map", max_items = 500)
            if len(searchResults) > 0:
                for result in searchResults:
                    dependencies = False
                    # Create list of Web Maps to search Web Apps
                    webmap = gis.content.get(result.id)
                    webMapDict = webmap.get_data(try_json=True)
                    webMapJSON = json.dumps(webMapDict)
                    try:
                        if item.url in webMapJSON or item.id in webMapJSON:
                            arcpy.AddMessage(f"--Service found in {webmap.title}")
                            webMapDependent = True
                            # Check if Web Map is in any Web Apps
                            dependencies = checkWebApps(webmap.id, dependencies)
                            if dependencies == False:
                                output = '{0},{1},{2},{3}\n'.format(item.title, item.id, webmap.title,
                                                                    webmap.id)
                                output_file.write(output)
                    except:
                        pass
        if webMapDependent == False:
           output = '{0},{1}\n'.format(item.title, item.id)
           output_file.write(output)
           arcpy.AddMessage("--{0} has no dependencies".format(item.title))

    elif contentType == 'Web Maps':
        # Check if Web Map is in any Web Apps
        dependencies = False
        dependencies = checkWebApps(item.id, dependencies)
        if dependencies == False:
           output = '{0},{1}\n'.format(item.title, item.id)
           output_file.write(output)
           arcpy.AddMessage("--{0} has no dependencies".format(item.title))

output_file.close()