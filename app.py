# Import the dependencies.

from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
import datetime as dt


#################################################
# Database Setup
#################################################


# reflect an existing database into a new model
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# reflect the tables
Base = automap_base()
Base.prepare(autoload_with=engine)
# Save references to each table

Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)


#################################################
# Flask Routes
#################################################

# Define the homepage route
@app.route("/")
def home():
    return (
        f"Welcome to the Climate App!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;"
    )

# Define the /api/v1.0/precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)

    # Calculate the date one year from the last date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)

    # Query precipitation data for the last 12 months
    results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago).all()

    session.close()

    # Convert the query results to a dictionary
    precipitation_data = {date: prcp for date, prcp in results}
    return jsonify(precipitation_data)

# Define the /api/v1.0/stations route
@app.route("/api/v1.0/stations")
def stations():
    # Create a new session for this route
    session = Session(engine)

    # Query to retrieve the list of stations
    results = session.query(Station.station).all()

    # Convert the results to a list
    station_list = [station for (station,) in results]

    # Close the session
    session.close()

    return jsonify(station_list)

# Define the /api/v1.0/tobs route
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    
    # Find the most active station
    most_active_station = session.query(Measurement.station).group_by(Measurement.station).\
        order_by(func.count().desc()).first()[0]
    
    # Calculate the date one year from the last date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)
    
    # Query temperature observations for the most active station for the last 12 months
    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station, Measurement.date >= one_year_ago).all()
    
    session.close()

    # Convert the query results to a list of dictionaries
    tobs_data = [{'Date': date, 'Temperature': tobs} for date, tobs in results]
    
    return jsonify(tobs_data)

# Define the /api/v1.0/<start> route
@app.route("/api/v1.0/<string:start>")
def calc_temps_start(start):
    session = Session(engine)

    try:
        start_date = dt.datetime.strptime(start, '%Y-%m-%d')
    except ValueError:
        session.close()
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."})

    # Query to calculate TMIN, TAVG, and TMAX for dates greater than or equal to the start date
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).all()

    # Close the session
    session.close()

    if results:
        # Convert the query results to a dictionary
        temp_data = {
            'TMIN': results[0][0],
            'TAVG': results[0][1],
            'TMAX': results[0][2]
        }
        return jsonify(temp_data)
    else:
        # Handle case where no data is found for the specified start date
        return jsonify({"error": "No data found for the specified start date."})

# Define the /api/v1.0/<start>/<end> route
@app.route("/api/v1.0/<string:start>/<string:end>")
def calc_temps_start_end(start, end):
    session = Session(engine)

    try:
        start_date = dt.datetime.strptime(start, '%Y-%m-%d')
        end_date = dt.datetime.strptime(end, '%Y-%m-%d')
    except ValueError:
        session.close()
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."})

    # Query to calculate TMIN, TAVG, and TMAX for dates between start and end (inclusive)
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date, Measurement.date <= end_date).all()

    # Close the session
    session.close()

    if results:
        # Convert the query results to a dictionary
        temp_data = {
            'TMIN': results[0][0],
            'TAVG': results[0][1],
            'TMAX': results[0][2]
        }
        return jsonify(temp_data)
    else:
        # Handle case where no data is found for the specified date range
        return jsonify({"error": "No data found for the specified date range."})

# Run the app
if __name__ == "__main__":
    app.run(debug=True)