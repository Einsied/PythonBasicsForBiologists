"""!
@package evaluate_survey
@brief This script is used to evaluate the survey for this course
@details The survey forms are produced as pdfs (survey.tex).
A printed form means it can be distributed and collected ensuring a high response
and accuracy of the survey.
It also prevents the accidental storing of idetifiable data.
Especially the respondent section is currently not anonymous for small study groups,
because the previous knowledge and enrollment may single out some students.

As a sample for the evaluation you may use survey_raw.json and fill it out for every module.
"""

import json
import pathlib
import numpy
import matplotlib.pyplot

def collect_results(survey_files:list)->tuple:
    """!
    @brief Iterate over all survey files and extract the fields
    @param survey_files the lsit containing the pathlib.Paths to the files
    @return a dict containing a dict for every tutor with a dict for the evalauted modules
        followed by the individual fields
    """
    # A dict containing the tutors as keys
    tutors = dict()
    # The rest of the fields
    fields = dict()

    module = 1
    for survey_file in survey_files:
        # Note this is a partial key it might be Tutor A, Tuttor B etc.
        TUTOR = "Tutor"
        # Fields in this list are not collected
        FIELDS_TO_IGNORE = ["Name", "Attended to learn"]
        with survey_file.open("r") as file_handle:
            content = json.load(file_handle)
            for key in content.keys(): 
                tutor_name = None
                current_field = content[key]
                if TUTOR in key:
                    current_field = content[key]
                    tutor_name = current_field["Name"]
                field_contents = dict()
                for current_field_key in current_field.keys():
                    if current_field_key not in FIELDS_TO_IGNORE:
                        field_contents[current_field_key] = current_field[current_field_key]
                if tutor_name is None:
                    if key not in fields:
                        fields[key] = dict()
                    fields[key][module] = field_contents
                else:
                    if tutor_name not in tutors:
                        tutors[tutor_name] = dict()
                    tutors[tutor_name][module] = field_contents
            module += 1
    return tutors, fields

def visualize_tutors(tutors:dict, plot_for_difference:float = 1.0, plot_for_std_over_time:float = 0.25)->None:
    """!
    @brief This function visaluzes the evaluation of the tutors
    @param tutors a dict contatining the tutor names as keys
    @param plot_for_difference is the threshold above we plot an aspect which differs siginficantly from the rest
    @param plot_for_std_over_time is the threshold of the standard deviation over all times over which we plot the results 
    """
    # For a good summary we should categorize into positive and negative aspects
    positive_aspect = ["Seems well prepared", "Treats participants with respect", "Understand explanations", "Confident to ask", "Taught on my level of knowledge", "Is good teacher"]
    negative_aspect = ["Style too frontal" , "Style too interactive"]

    def get_fields_over_time(tutor_modules:dict)->dict:
        """!
        @brief Collects the entry for every field for every module
        @details This just changes dimentsions for easier handling
        @param tutor_modules a dict containing the module numbers as keys
        @return a dict containing the module numbers as keys and the means, medians and standard-deviations as values
        """
        fields_over_time = dict()
        for module in tutor_modules.keys():
            current_module = tutor_modules[module]
            # Get all fields this module to compare them
            module_results = dict()
            for field in current_module.keys():
                field_values = current_module[field]
                if field not in fields_over_time:
                    fields_over_time[field] = dict()
                is_positive = True
                if field in positive_aspect:
                    is_positive = True
                elif field in negative_aspect:
                    is_positive = False
                else:
                    print(f"Failed to treat field \"{field}\" in module {module} for tutor {tutor}")
                field_scores = list()
                for answer_index in range(0, len(field_values), 1):
                    answer_score = answer_index + 1
                    if is_positive:
                        answer_score = len(field_values)  - answer_score + 1
                    for number_of_answers in range(0, field_values[answer_index], 1):
                        field_scores.append(answer_score)
                field_mean = numpy.mean(field_scores)
                field_median = numpy.median(field_scores)
                field_std = numpy.std(field_scores)
                # Consider plotting here to get insight into each module instead of the devlopment over time
                fields_over_time[field][module] = {"Mean":field_mean, "Median": field_median, "Std": field_std}
        return fields_over_time

    # Process every tutor separatley
    for tutor in tutors:
        # Get an overall time development
        tutor_modules = tutors[tutor]
        fields_over_time = get_fields_over_time(tutor_modules)
        module_averages = dict()
        for field in fields_over_time.keys():
            field_over_time = fields_over_time[field]
            for module in field_over_time.keys():
                if module not in module_averages:
                    module_averages[module] = list()
                module_averages[module].append(field_over_time[module]["Mean"])
        tutor_rating_per_module = list()
        modules = list()
        for module in module_averages.keys():
            tutor_rating_per_module.append(numpy.mean(module_averages[module]))
            modules.append(module)
        tutor_rating = numpy.mean(tutor_rating_per_module)

        worth_plotting = list()
        for field in fields_over_time.keys():
            values = list()
            modules = list()
            field_over_time = fields_over_time[field]
            for module in field_over_time.keys():
                values.append(field_over_time[module]["Mean"])
                modules.append(module)
            mean = numpy.mean(values)
            std = numpy.std(values)
            if std > plot_for_std_over_time or abs(tutor_rating - mean) > plot_for_difference:
                to_plot = (field, values, modules)
                worth_plotting.append(to_plot)

        # Time to plot
        matplotlib.pyplot.title(f"Tutor {tutor}: {tutor_rating:.2f}")
        matplotlib.pyplot.plot(modules, tutor_rating_per_module, label = "Tutor rating")
        for plot_index in range(0, len(worth_plotting), 1):
            field_name, y, x = worth_plotting[plot_index]
            matplotlib.pyplot.plot(x, y, label=field_name)
            
        matplotlib.pyplot.ylim(1, 5)
        matplotlib.pyplot.ylabel("Aggreement")
        matplotlib.pyplot.xlabel("Module")
        matplotlib.pyplot.legend()
        matplotlib.pyplot.show()

def visualize_respondents(respondents:dict)->None:
    """!
    @brief This function visualizes the respondents distribution
    @param fields a dict contatining the fields for the repondents
    """
    # Sorting by field and module instead of the other way around
    fields = dict() 
    for module in respondents.keys():
        fields_in_module = respondents[module]
        for field in fields_in_module.keys():
            field_content = fields_in_module[field]
            if field not in fields:
                fields[field] = dict()
            field_scores = list()
            for answer_index in range(0, len(field_content), 1):
                answers = field_content[answer_index]
                for response in range(0, answers, 1):
                    field_scores.append(len(field_content) - answer_index)
            fields[field][module] = field_scores
    fig, axes = matplotlib.pyplot.subplots(len(fields.keys()), 1)
    fig.suptitle("Respondents")
    bins = numpy.arange(0.5, 6, 1.0)
    for field_index in range(0, len(fields.keys()), 1):
        field = list(fields.keys())[field_index]
        axes[field_index].set_title(field)
        axes[field_index].set_xlim(min(bins), max(bins))
        axes[field_index].set_ylabel("Responses")
        axes[field_index].set_xlabel("Module")
        field_modules = fields[field]
        axes[field_index].hist([field_modules[module] for module in field_modules.keys()], label=[f"Module {module}" for module in field_modules.keys()], bins = bins )
        axes[field_index].set_xticks([min(bins), max(bins)])
        axes[field_index].set_xticklabels(["Disagree", "Agree"])
        axes[field_index].legend()
    matplotlib.pyplot.show()

def get_plots_for_field(field:dict, field_name:str, plot_for_difference:float, plot_for_std_over_time:float)->list:
    """!
    @brief This function creates tuples for plotting
    @param fields a dict contatining the sub_fields for the field
    @param field_name the name of the field we are evaluating
    @param plot_for_difference is the threshold above we plot an aspect which differs siginficantly from the rest
    @param plot_for_std_over_time is the threshold of the standard deviation over all times over which we plot the results
        separately for the time
    @return a list of tuples containing the name of the (plot, x-values, y-values)
    """
    # We need to define positive and engative sub-fields for a ranking
    positive_aspect = [
        # Example
        "Motivating", "Understood", "Easy to understand", "Introduced contents naturally", "The example should be kept",
        # Presentation
        "Materials are helpful", "Materials replace notes", "Materials work without major problems",
        # Content
        "Well structured", "Follow with ease", "Relevance",
        # Atmosphere
        "Like to work with other participants",
        # Summary
        "Is useful", "Wish to attend earlier", "Would recommend"
    ]
    negative_aspect = [
        # Example has no negative aspects
        # Presentation
        "Materials are too verbose", "Materials are too short", "Materials are too formal",  "Materials are too colloquial", 
        # Content
        "Too theoretical", "Too practical",
        # Atmosphere
        "Stress", "Excluded", "Unsafe"
        # Summary has no negative aspects
    ]

    def get_fields_over_time(modules:dict)->dict:
        """!
        @brief Collects the entry for every sub_field for every module
        @details This just changes dimentsions for easier handling
        @param modules a dict containing the module numbers as keys
        @return a dict containing the module numbers as keys and the means, medians and standard-deviations as values
        """
        fields_over_time = dict()
        for module in modules.keys():
            current_module = modules[module]
            # Get all fields this module to compare them
            module_results = dict()
            for field in current_module.keys():
                field_values = current_module[field]
                if field not in fields_over_time:
                    fields_over_time[field] = dict()
                is_positive = True
                if field in positive_aspect:
                    is_positive = True
                elif field in negative_aspect:
                    is_positive = False
                else:
                    print(f"Failed to treat sub-field \"{field}\" in module {module} for field {field_name}")
                field_scores = list()
                for answer_index in range(0, len(field_values), 1):
                    answer_score = answer_index + 1
                    if is_positive:
                        answer_score = len(field_values)  - answer_score + 1
                    for number_of_answers in range(0, field_values[answer_index], 1):
                        field_scores.append(answer_score)
                field_mean = numpy.mean(field_scores)
                field_median = numpy.median(field_scores)
                field_std = numpy.std(field_scores)
                # Consider plotting here to get insight into each module instead of the devlopment over time
                fields_over_time[field][module] = {"Mean":field_mean, "Median": field_median, "Std": field_std}
        return fields_over_time

    # Process every tutor separatley
    fields_over_time = get_fields_over_time(field)
    module_averages = dict()
    for field in fields_over_time.keys():
        field_over_time = fields_over_time[field]
        for module in field_over_time.keys():
            if module not in module_averages:
                module_averages[module] = list()
            module_averages[module].append(field_over_time[module]["Mean"])
    field_rating_per_module = list()
    modules = list()
    for module in module_averages.keys():
        field_rating_per_module.append(numpy.mean(module_averages[module]))
        modules.append(module)
    field_rating = numpy.mean(field_rating_per_module)

    worth_plotting = [(f"{field} rating", field_rating_per_module, modules)]
    for field in fields_over_time.keys():
        values = list()
        modules = list()
        field_over_time = fields_over_time[field]
        for module in field_over_time.keys():
            values.append(field_over_time[module]["Mean"])
            modules.append(module)
        mean = numpy.mean(values)
        std = numpy.std(values)
        if std > plot_for_std_over_time or abs(field_rating - mean) > plot_for_difference:
            to_plot = (field, values, modules)
            worth_plotting.append(to_plot)
    return worth_plotting

def visualize_fields(fields:dict, plot_for_difference:float = 1.0, plot_for_std_over_time:float = 0.25)->None:
    """!
    @brief This function visalulizes the evaluation of the fields
    @param fields a dict contatining the overarching concepts as keys and dicts with teh fields
    @param plot_for_difference is the threshold above we plot an aspect which differs siginficantly from the rest
    @param plot_for_std_over_time is the threshold of the standard deviation over all times over which we plot the results 
    """
    #visualize_respondents(fields["Respondent"])
    field_names = [
        "Example",
        "Presentation",
        "Content",
        "Atmosphere",
        "Summary"
    ]
    for field_name in field_names:
        to_plot = get_plots_for_field(fields[field_name], field_name, plot_for_difference, plot_for_std_over_time)
        label, values, modules = to_plot[0]
        matplotlib.pyplot.plot(modules, values, label=label)
        matplotlib.pyplot.title(f"{field_name}: {numpy.mean(values):0.2f}")
        if len(to_plot) > 1:
            for plot_index in range(1, len(to_plot), 1):
                label, values, modules = to_plot[plot_index]
                matplotlib.pyplot.plot(modules, values, label = label)
        matplotlib.pyplot.xlim(1, 5)
        matplotlib.pyplot.ylim(1, 5)
        matplotlib.pyplot.legend()
        matplotlib.pyplot.show()


survey_data_path = pathlib.Path("./")
# Storing the survey files in an ordered list
survey_files = [
    survey_data_path / "survey_1.json",
    survey_data_path / "survey_2.json",
    survey_data_path / "survey_3.json",
    survey_data_path / "survey_4.json",
    survey_data_path / "survey_5.json"
]

tutors, fields = collect_results(survey_files)
visualize_tutors(tutors)
visualize_fields(fields)
